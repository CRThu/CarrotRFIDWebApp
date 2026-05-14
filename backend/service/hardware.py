import asyncio
from typing import Optional
from loguru import logger

# 引入核心库
from crft.drivers.pn532_hsu import PN532_HSU
from crft.hardware.serial_transport import SerialTransport

class HardwareManager:
    """硬件管理单例"""
    def __init__(self):
        self.reader: Optional[PN532_HSU] = None
        self.transport: Optional[SerialTransport] = None
        self.lock = asyncio.Lock()
        self.port: str = ""
        self.baudrate: int = 115200

    def connect(self, port: str, baudrate: int = 115200, reader_type: str = "pn532") -> bool:
        """连接设备"""
        try:
            if self.reader:
                self.disconnect()
            logger.info(f"正在初始化硬件 - 类型: {reader_type}, 串口: {port}, 波特率: {baudrate}")
            self.transport = SerialTransport(port=port, baudrate=baudrate)
            
            if reader_type.lower() == "pn532":
                self.reader = PN532_HSU(self.transport)
            else:
                raise ValueError(f"不支持的读卡器类型: {reader_type}")

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

hw = HardwareManager()
