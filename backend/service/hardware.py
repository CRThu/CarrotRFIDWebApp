import asyncio
from typing import Optional
from loguru import logger

# 引入核心库
from crft.drivers.pn532_hsu import PN532_HSU
from crft.hardware.serial_transport import SerialTransport
import serial.tools.list_ports

class HardwareManager:
    """硬件管理单例"""
    def __init__(self):
        self.reader: Optional[PN532_HSU] = None
        self.transport: Optional[SerialTransport] = None
        self.lock = asyncio.Lock()
        self.port: str = ""
        self.baudrate: int = 115200

    def get_available_ports(self) -> list[str]:
        """获取所有可用串口"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def get_supported_readers(self) -> list[str]:
        """获取支持的读卡器类型（从驱动包中动态查找）"""
        import crft.drivers
        readers = []
        for name in getattr(crft.drivers, "__all__", []):
            if name != "CardReader":
                readers.append(name)
        return readers if readers else ["PN532_HSU"]

    def connect(self, port: str, baudrate: int = 115200, reader_type: str = "PN532_HSU") -> bool:
        """连接设备"""
        try:
            if self.reader:
                self.disconnect()
            logger.info(f"正在初始化硬件 - 类型: {reader_type}, 串口: {port}, 波特率: {baudrate}")
            self.transport = SerialTransport(port=port, baudrate=baudrate)
            
            import crft.drivers
            reader_class = getattr(crft.drivers, reader_type, None)
            if not reader_class:
                raise ValueError(f"不支持的读卡器类型: {reader_type}")
            
            self.reader = reader_class(self.transport)

            self.reader.connect()
            # 简单自检
            version = self.reader.get_version()
            if version:
                logger.info(f"硬件初始化成功, 固件版本: {version.hex().upper()}")
            else:
                logger.warning("获取版本号失败，但串口已打开")
            self.port = port
            self.baudrate = baudrate
            return True
        except Exception as e:
            logger.error(f"硬件初始化失败: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """断开设备"""
        try:
            if self.reader:
                self.reader.disconnect()
        except Exception as e:
            logger.error(f"断开读卡器异常: {e}")
        finally:
            self.reader = None
            if self.transport:
                self.transport.close()
                self.transport = None
            self.port = ""
            logger.info("硬件已断开")

    def get_target(self) -> Optional[dict]:
        """侦测当前卡片"""
        if not self.reader:
            return None
        try:
            target = self.reader.find()
            if target:
                return {
                    "uid": target["uid"].hex().upper(),
                    "sak": hex(target["sak"]).upper(),
                    "type": self._guess_card_type(target["sak"])
                }
        except Exception:
            pass
        return None

    def set_config(self, tx_crc: bool, rx_crc: bool):
        """配置硬件参数"""
        if self.reader:
            self.reader.set_crc(tx_crc, rx_crc)

    def _guess_card_type(self, sak: int) -> str:
        """根据 SAK 简单猜测卡片类型"""
        if sak == 0x08: return "Mifare Classic 1K"
        if sak == 0x18: return "Mifare Classic 4K"
        if sak == 0x20: return "Mifare Desfire / JCOP"
        if sak == 0x28: return "Mifare Classic 1K (Emulated)"
        if sak == 0x00: return "Mifare Ultralight / NTAG"
        return f"Unknown (SAK: {hex(sak)})"

hw = HardwareManager()
