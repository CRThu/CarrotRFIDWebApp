<template>
  <div class="h-screen flex flex-col bg-base-300 p-4 gap-4 overflow-hidden" data-theme="dark">
    <!-- 头部导航 -->
    <div class="navbar bg-base-100 rounded-box shadow-lg px-6">
      <div class="flex-1">
        <a class="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent flex items-center gap-2">
          <ZapIcon class="text-primary" :size="24" />
          CarrotRFID Web Console
        </a>
      </div>
      <div class="flex-none gap-4">
        <div class="stats bg-base-200 shadow scale-90">
          <div class="stat py-2 px-4">
            <div class="stat-title">System Status</div>
            <div class="stat-value text-sm flex items-center gap-2" :class="isConnected ? 'text-success' : 'text-error'">
              <div class="badge badge-xs" :class="isConnected ? 'badge-success' : 'badge-error'"></div>
              {{ isConnected ? 'CONNECTED' : 'DISCONNECTED' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="flex-1 flex flex-col md:flex-row gap-4 min-h-0">
      <!-- 左侧控制面板 -->
      <div class="w-full md:w-80 flex flex-col gap-4">
        <!-- 硬件配置 -->
        <div class="bg-base-100 rounded-box shadow-lg p-6 border border-base-200">
          <h2 class="font-bold flex items-center gap-2 mb-4 text-primary">
            <SettingsIcon :size="18" /> Hardware Config
          </h2>
          
          <div class="form-control w-full gap-3">
            <div>
              <label class="label"><span class="label-text">Serial Port</span></label>
              <select v-model="config.port" class="select select-bordered select-sm w-full font-mono" :disabled="isConnected">
                <option v-for="p in options.ports" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>

            <div>
              <label class="label"><span class="label-text">Baud Rate</span></label>
              <select v-model="config.baudrate" class="select select-bordered select-sm w-full" :disabled="isConnected">
                <option v-for="b in options.baudrates" :key="b" :value="b">{{ b }}</option>
              </select>
            </div>

            <div>
              <label class="label"><span class="label-text">Reader Type</span></label>
              <select v-model="config.reader_type" class="select select-bordered select-sm w-full" :disabled="isConnected">
                <option v-for="r in options.readers" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>

            <div class="mt-4 flex flex-col gap-2">
              <button 
                v-if="!isConnected"
                class="btn btn-primary btn-sm w-full" 
                @click="connectHardware"
                :disabled="loading.connect"
              >
                <span v-if="loading.connect" class="loading loading-spinner loading-xs"></span>
                CONNECT
              </button>
              <button 
                v-else
                class="btn btn-error btn-outline btn-sm w-full" 
                @click="disconnectHardware"
                :disabled="loading.connect"
              >
                DISCONNECT
              </button>
            </div>
          </div>
        </div>

        <!-- 快速指令 (可选) -->
        <div class="bg-base-100 rounded-box shadow-lg p-6 border border-base-200 flex-1 overflow-hidden flex flex-col">
          <h2 class="font-bold flex items-center gap-2 mb-4 text-secondary">
            <BookmarkIcon :size="18" /> Favorites
          </h2>
          <div class="flex-1 overflow-y-auto space-y-2 pr-2">
            <button 
              v-for="fav in favorites" 
              :key="fav.name"
              class="btn btn-ghost btn-xs w-full justify-start font-mono text-xs opacity-70 hover:opacity-100"
              @click="cmdHex = fav.hex"
            >
              {{ fav.name }}
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧内容区 -->
      <div class="flex-1 flex flex-col gap-4 min-h-0">
        <!-- 日志面板 -->
        <div class="flex-1 flex flex-col bg-base-100 rounded-box shadow-lg border border-base-200 overflow-hidden">
          <div class="p-4 border-b border-base-200 flex justify-between items-center bg-base-200/30">
            <h2 class="font-bold flex items-center gap-2">
              <TerminalIcon :size="18" class="text-info" /> Real-time Logs
            </h2>
            <div class="flex gap-2 items-center">
              <div class="join">
                <button 
                  v-for="level in ['DEBUG', 'INFO', 'WARN', 'ERROR']" 
                  :key="level"
                  class="btn btn-xs join-item"
                  :class="activeFilters.includes(level) ? levelClass(level) : 'btn-ghost'"
                  @click="toggleFilter(level)"
                >
                  {{ level }}
                </button>
              </div>
              <button class="btn btn-xs btn-outline btn-error" @click="clearLogs">Clear</button>
            </div>
          </div>
          
          <div class="flex-1 overflow-y-auto p-4 mockup-code bg-neutral text-neutral-content rounded-none m-0 scroll-smooth" ref="logViewport">
            <pre v-for="(log, index) in filteredLogs" :key="index" :data-prefix="'>'" :class="levelTextClass(log.level)">
              <code><span class="opacity-40 text-[10px]">{{ formatTime(log.timestamp) }}</span> <span class="font-bold">[{{ log.level }}]</span> {{ log.message }}</code>
            </pre>
            <div v-if="filteredLogs.length === 0" class="text-center opacity-20 mt-10 italic">Waiting for telemetry...</div>
          </div>
        </div>

        <!-- 指令面板 -->
        <div class="bg-base-100 rounded-box shadow-lg p-6 border border-base-200">
          <div class="flex flex-col gap-4">
            <h2 class="font-bold flex items-center gap-2 text-accent">
              <CpuIcon :size="18" /> Transceive Debugger
            </h2>
            <div class="join w-full shadow-sm">
              <input 
                v-model="cmdHex" 
                type="text" 
                placeholder="Enter Hex (e.g. 00 00 FF 03 FD D4 14 01 17 00)" 
                class="input input-bordered join-item flex-1 font-mono focus:input-accent"
                @keyup.enter="sendCmd"
              />
              <button 
                class="btn btn-accent join-item px-8" 
                :disabled="!isConnected || loading.send"
                @click="sendCmd"
              >
                <span v-if="loading.send" class="loading loading-spinner loading-xs"></span>
                SEND
              </button>
            </div>
            
            <div v-if="lastResponse" class="collapse collapse-arrow bg-base-200 border border-base-300 overflow-hidden">
              <input type="checkbox" checked /> 
              <div class="collapse-title text-sm font-medium opacity-70 flex items-center gap-2">
                <ChevronRightIcon :size="14" /> Last Response
              </div>
              <div class="collapse-content"> 
                <div class="bg-black/40 p-4 rounded font-mono text-success break-all border border-success/20">
                  {{ lastResponse }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick, reactive } from 'vue'
import { 
  Terminal as TerminalIcon, 
  Cpu as CpuIcon, 
  Settings as SettingsIcon, 
  Zap as ZapIcon,
  Bookmark as BookmarkIcon,
  ChevronRight as ChevronRightIcon
} from 'lucide-vue-next'

// 状态定义
const isConnected = ref(false)
const cmdHex = ref('')
const lastResponse = ref('')
const loading = reactive({
  connect: false,
  send: false
})
const logs = ref([])
const activeFilters = ref(['DEBUG', 'INFO', 'WARN', 'ERROR'])
const logViewport = ref(null)

const options = reactive({
  ports: [],
  readers: [],
  baudrates: []
})

const config = reactive({
  port: '',
  baudrate: 115200,
  reader_type: 'PN532_HSU'
})

const favorites = [
  { name: 'PN532 Get Firmware', hex: '00 00 FF 02 FE D4 02 2A 00' },
  { name: 'PN532 SAM Config', hex: '00 00 FF 05 FB D4 14 01 14 01 02 00' },
  { name: 'InListPassiveTarget', hex: '00 00 FF 04 FC D4 4A 01 00 E1 00' }
]

// 计算属性
const filteredLogs = computed(() => {
  return logs.value.filter(log => activeFilters.value.includes(log.level))
})

// 样式工具
const levelClass = (level) => {
  switch(level) {
    case 'ERROR': return 'btn-error text-white'
    case 'WARN': return 'btn-warning text-white'
    case 'INFO': return 'btn-info text-white'
    default: return 'btn-neutral'
  }
}

const levelTextClass = (level) => {
  switch(level) {
    case 'ERROR': return 'text-error'
    case 'WARN': return 'text-warning'
    case 'INFO': return 'text-info'
    default: return 'text-neutral-content opacity-70'
  }
}

// 逻辑处理
const toggleFilter = (level) => {
  const index = activeFilters.value.indexOf(level)
  if (index > -1) activeFilters.value.splice(index, 1)
  else activeFilters.value.push(level)
}

const clearLogs = () => logs.value = []

const formatTime = (isoStr) => {
  if (!isoStr) return '--:--:--'
  const date = new Date(isoStr)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

watch(filteredLogs, () => {
  nextTick(() => {
    if (logViewport.value) {
      logViewport.value.scrollTop = logViewport.value.scrollHeight
    }
  })
}, { deep: true })

// API 交互
const connectWS = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/logs`)

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      logs.value.push(data)
      if (logs.value.length > 1000) logs.value.shift()
    } catch(e) {}
  }

  ws.onclose = () => setTimeout(connectWS, 2000)
}

const fetchOptions = async () => {
  try {
    const res = await fetch('/api/hardware/options')
    const data = await res.json()
    options.ports = data.ports
    options.readers = data.readers
    options.baudrates = data.baudrates
    
    // 默认选择第一个
    if (!config.port && options.ports.length > 0) config.port = options.ports[0]
    if (!config.reader_type && options.readers.length > 0) config.reader_type = options.readers[0]
  } catch (e) {}
}

const checkStatus = async () => {
  try {
    const res = await fetch('/api/hardware/status')
    const data = await res.json()
    isConnected.value = data.connected
    if (isConnected.value) {
      config.port = data.port
      config.baudrate = data.baudrate
    }
  } catch (e) {
    isConnected.value = false
  }
}

const connectHardware = async () => {
  if (!config.port) {
    alert('Please select a serial port')
    return
  }
  loading.connect = true
  try {
    const res = await fetch('/api/hardware/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    })
    const data = await res.json()
    if (res.ok) {
      isConnected.value = true
    } else {
      alert(data.detail || 'Connection failed')
    }
  } catch (e) {
    alert('Network error')
  } finally {
    loading.connect = false
  }
}

const disconnectHardware = async () => {
  loading.connect = true
  try {
    await fetch('/api/hardware/disconnect', { method: 'POST' })
    isConnected.value = false
  } catch (e) {
    alert('Disconnect failed')
  } finally {
    loading.connect = false
  }
}

const sendCmd = async () => {
  if (!cmdHex.value || loading.send) return
  loading.send = true
  lastResponse.value = ''
  try {
    const res = await fetch('/api/cmd/transceive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hex: cmdHex.value })
    })
    const data = await res.json()
    if (res.ok) {
      lastResponse.value = data.response
    } else {
      alert(data.detail || 'Command failed')
    }
  } catch (e) {
    alert('Network error')
  } finally {
    loading.send = false
  }
}

onMounted(() => {
  connectWS()
  fetchOptions()
  checkStatus()
  setInterval(checkStatus, 3000)
})
</script>

<style>
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: rgba(255,255,255,0.1);
  border-radius: 10px;
}

/* 渐变背景效果 */
.bg-base-100 {
  background-color: hsl(var(--b1) / 0.8);
  backdrop-filter: blur(12px);
}
</style>
