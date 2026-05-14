<template>
  <div class="h-screen flex flex-col bg-base-300 overflow-hidden" data-theme="dark">
    <!-- Top Header -->
    <header class="navbar bg-base-100 border-b border-base-200 px-6 min-h-12 shadow-sm z-10">
      <div class="flex-1">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-primary/10 rounded-lg">
            <ZapIcon class="text-primary" :size="20" />
          </div>
          <h1 class="text-lg font-bold tracking-tight">CarrotRFID <span class="text-primary">Workbench</span></h1>
        </div>
      </div>
      <div class="flex-none flex items-center gap-4">
        <div class="flex items-center gap-2 px-3 py-1 bg-base-200 rounded-full text-xs font-mono border border-base-300">
          <div class="badge badge-xs" :class="isConnected ? 'badge-success shadow-[0_0_8px_#36d399]' : 'badge-error'"></div>
          <span :class="isConnected ? 'text-success' : 'text-error'">{{ isConnected ? 'HARDWARE ONLINE' : 'OFFLINE' }}</span>
        </div>
      </div>
    </header>

    <!-- Main Content Grid -->
    <main class="flex-1 flex overflow-hidden p-2 gap-2">
      
      <!-- Left: Control Panel -->
      <aside class="w-72 flex flex-col gap-2">
        <!-- 1. Hardware Config -->
        <section class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden shrink-0">
          <div class="p-4 border-b border-base-200 bg-base-200/50 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <SettingsIcon :size="16" class="text-primary" />
              <h2 class="text-sm font-bold opacity-80 uppercase tracking-wider">Device Settings</h2>
            </div>
            <button class="btn btn-ghost btn-xs" @click="refreshPorts" :disabled="isConnected">
              <RotateCcwIcon :size="12" />
            </button>
          </div>
          <div class="p-4 space-y-3">
            <div class="space-y-1">
              <label class="text-[10px] font-bold opacity-50 uppercase pl-1">Serial Port</label>
              <select v-model="config.port" class="select select-bordered select-xs w-full font-mono" :disabled="isConnected">
                <option v-for="p in options.ports" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div class="space-y-1">
                <label class="text-[10px] font-bold opacity-50 uppercase pl-1">Baud Rate</label>
                <select v-model="config.baudrate" class="select select-bordered select-xs w-full" :disabled="isConnected">
                  <option v-for="b in options.baudrates" :key="b" :value="b">{{ b }}</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="text-[10px] font-bold opacity-50 uppercase pl-1">Reader</label>
                <select v-model="config.reader_type" class="select select-bordered select-xs w-full" :disabled="isConnected">
                  <option v-for="r in options.readers" :key="r" :value="r">{{ r }}</option>
                </select>
              </div>
            </div>
            <button 
              v-if="!isConnected"
              class="btn btn-primary btn-sm w-full mt-2" 
              @click="connectHardware"
              :disabled="loading.connect"
            >
              <span v-if="loading.connect" class="loading loading-spinner loading-xs"></span>
              INIT HARDWARE
            </button>
            <button 
              v-else
              class="btn btn-outline btn-error btn-sm w-full mt-2" 
              @click="disconnectHardware"
            >
              DISCONNECT
            </button>
          </div>
        </section>

        <!-- 2. Target Context -->
        <section class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden flex-1">
          <div class="p-4 border-b border-base-200 bg-base-200/50 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <ScanIcon :size="16" class="text-secondary" />
              <h2 class="text-sm font-bold opacity-80 uppercase tracking-wider">Target Info</h2>
            </div>
          </div>
          <div class="p-4 flex flex-col items-center gap-2">
            <div class="relative">
              <div class="w-20 h-20 rounded-full border-4 flex items-center justify-center transition-all duration-500"
                   :class="target.uid ? 'border-success bg-success/5 shadow-[0_0_20px_rgba(54,211,153,0.2)]' : 'border-base-300 opacity-20'">
                <CreditCardIcon :size="32" :class="target.uid ? 'text-success' : 'text-base-content'" />
              </div>
              <div v-if="target.uid" class="absolute -bottom-1 -right-1 badge badge-success badge-sm shadow-md border-base-100">DETECTED</div>
            </div>
            
            <div class="w-full space-y-4 pt-2">
              <div class="text-center">
                <div class="text-[10px] font-bold opacity-30 uppercase tracking-widest mb-1">Card Type</div>
                <div class="text-sm font-semibold truncate">{{ target.type || 'N/A' }}</div>
              </div>
              <div class="divider my-0 opacity-20"></div>
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-[10px] font-bold opacity-40">UID</span>
                  <span class="font-mono text-xs font-bold text-secondary">{{ target.uid || '---- ----' }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-[10px] font-bold opacity-40">SAK</span>
                  <span class="font-mono text-xs">{{ target.sak || '00' }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-auto p-4 bg-base-200/30 border-t border-base-200 grid grid-cols-2 gap-2">
            <button class="btn btn-secondary btn-sm" :disabled="!isConnected" @click="fetchTarget">
              <SearchIcon :size="14" class="mr-1" /> SCAN
            </button>
            <button class="btn btn-sm" :class="autoScan ? 'btn-error' : 'btn-outline'" :disabled="!isConnected" @click="autoScan = !autoScan">
              {{ autoScan ? 'STOP' : 'AUTO' }}
            </button>
          </div>
        </section>
      </aside>

      <!-- Center: Instruction Commander -->
      <section class="flex-1 flex flex-col gap-2 min-w-0">
        <!-- 3. Library & Workbench -->
        <div class="card bg-base-100 shadow-xl border border-base-200 flex-1 overflow-hidden flex flex-col">
          <div class="p-1.5 border-b border-base-200 bg-base-200/50 flex items-center gap-1 overflow-x-auto no-scrollbar">
            <button 
              v-for="cat in categories" 
              :key="cat"
              class="btn btn-xs"
              :class="activeCategory === cat ? 'btn-primary' : 'btn-ghost opacity-60'"
              @click="activeCategory = cat"
            >
              {{ cat }}
            </button>
          </div>
          
          <div class="flex-1 overflow-y-auto p-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              <div 
                v-for="item in presets" 
                :key="item.name"
                class="group p-2.5 bg-base-200 hover:bg-primary/5 border border-base-300 hover:border-primary/30 rounded-xl cursor-pointer transition-all active:scale-95 flex flex-col gap-0.5"
                @click="injectPreset(item)"
              >
                <div class="flex justify-between items-start">
                  <span class="text-xs font-bold truncate group-hover:text-primary transition-colors">{{ item.name }}</span>
                  <ArrowUpRightIcon :size="12" class="opacity-0 group-hover:opacity-40 transition-opacity" />
                </div>
                <span class="text-[10px] opacity-40 line-clamp-1 italic">{{ item.desc }}</span>
                <div class="mt-1.5 font-mono text-[9px] opacity-30 group-hover:opacity-100 transition-opacity truncate bg-black/20 px-1.5 py-0.5 rounded">
                  {{ item.hex }}
                </div>
              </div>
            </div>
          </div>

          <!-- Command Debugger / Editor -->
          <div class="p-4 bg-base-200/50 border-t border-base-200">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-xs font-bold uppercase tracking-widest opacity-50 flex items-center gap-2">
                <TerminalIcon :size="14" /> Command Editor
              </h3>
              <div class="flex items-center gap-4">
                <label class="flex items-center gap-2 cursor-pointer group">
                  <span class="text-[10px] font-bold opacity-40 group-hover:opacity-100 transition-opacity">TX CRC</span>
                  <input type="checkbox" v-model="txCrc" class="toggle toggle-primary toggle-xs" @change="updateConfig" />
                </label>
                <label class="flex items-center gap-2 cursor-pointer group">
                  <span class="text-[10px] font-bold opacity-40 group-hover:opacity-100 transition-opacity">RX CRC</span>
                  <input type="checkbox" v-model="rxCrc" class="toggle toggle-primary toggle-xs" @change="updateConfig" />
                </label>
                <button class="btn btn-ghost btn-xs ml-2" @click="cmdHex = ''">CLEAR</button>
              </div>
            </div>

            <div class="flex gap-3 items-end">
              <div class="flex-1 space-y-2">
                <div class="relative group">
                  <textarea 
                    v-model="cmdHex" 
                    placeholder="Enter High-Level Hex Command (e.g. 30 04)" 
                    class="textarea textarea-bordered w-full font-mono text-xs leading-relaxed bg-neutral h-20 focus:border-primary transition-colors shadow-inner no-scrollbar"
                    @keydown.ctrl.enter="sendCmd"
                  ></textarea>
                  <div class="absolute bottom-2 right-2 text-[10px] opacity-20 pointer-events-none group-hover:opacity-40 transition-opacity">Ctrl + Enter to send</div>
                </div>
              </div>
              <button 
                class="btn btn-primary btn-lg px-8 h-20 flex flex-col gap-1 shadow-lg shadow-primary/20" 
                :disabled="!isConnected || loading.send"
                @click="sendCmd"
              >
                <ZapIcon v-if="!loading.send" :size="24" />
                <span v-else class="loading loading-spinner loading-md"></span>
                <span class="text-[10px] font-bold tracking-tighter">SEND</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Right: Monitor Panel -->
      <aside class="w-96 flex flex-col gap-2">
        <div class="card bg-base-100 shadow-xl border border-base-200 flex-1 overflow-hidden flex flex-col">
          <div class="tabs tabs-boxed bg-base-200/50 rounded-none border-b border-base-200 p-1">
            <button 
              class="tab tab-sm flex-1 font-bold" 
              :class="monitorTab === 'logs' ? 'tab-active' : ''"
              @click="monitorTab = 'logs'"
            >
              REAL-TIME LOGS
            </button>
            <button 
              class="tab tab-sm flex-1 font-bold" 
              :class="monitorTab === 'history' ? 'tab-active' : ''"
              @click="monitorTab = 'history'"
            >
              HISTORY
            </button>
          </div>

          <!-- Log View -->
          <div v-show="monitorTab === 'logs'" class="flex-1 flex flex-col overflow-hidden">
            <div class="p-2 border-b border-base-200 flex justify-between items-center px-4">
              <div class="flex gap-1">
                <button 
                  v-for="lvl in ['DRIVER', 'PROTOCOL', 'DEBUG', 'INFO', 'WARN', 'ERROR']" 
                  :key="lvl"
                  class="btn btn-[8px] btn-ghost px-2 h-5 min-h-0 text-[8px]"
                  :class="activeFilters.includes(lvl) ? levelClass(lvl) : 'opacity-40'"
                  @click="toggleFilter(lvl)"
                >
                  {{ lvl }}
                </button>
              </div>
              <button class="btn btn-ghost btn-xs text-[10px]" @click="clearLogs">CLEAR</button>
            </div>
            <div class="flex-1 overflow-y-auto p-3 font-mono bg-black/40 text-neutral-content rounded-none m-0 text-[10px] leading-relaxed scroll-smooth" ref="logViewport">
              <div v-for="(log, index) in filteredLogs" :key="index" :class="levelTextClass(log.level)" class="hover:bg-white/5 transition-colors cursor-default py-0.5 border-b border-white/5 last:border-0 flex gap-2">
                <span class="opacity-30 shrink-0 select-none">{{ formatTime(log.timestamp) }}</span>
                <span class="font-bold shrink-0 select-none">[{{ log.level }}]</span>
                <span class="break-all whitespace-pre-wrap">{{ log.message }}</span>
              </div>
              <div v-if="filteredLogs.length === 0" class="text-center opacity-10 mt-20 italic select-none uppercase tracking-widest">Listening for data...</div>
            </div>
          </div>

          <!-- History View -->
          <div v-show="monitorTab === 'history'" class="flex-1 overflow-y-auto p-3 space-y-2 bg-base-200/20">
            <div 
              v-for="(item, idx) in history" 
              :key="idx" 
              class="p-2 bg-base-100 border border-base-200 rounded-lg hover:border-primary/40 cursor-pointer transition-all group"
              @click="cmdHex = item.hex"
            >
              <div class="flex justify-between items-center mb-1">
                <span class="text-[9px] font-mono opacity-40">{{ formatTime(item.timestamp) }}</span>
                <span class="badge badge-ghost badge-xs text-[8px] opacity-0 group-hover:opacity-100 transition-opacity">RESTORE</span>
              </div>
              <div class="font-mono text-[10px] break-all group-hover:text-primary transition-colors">{{ item.hex }}</div>
              <div v-if="item.response" class="mt-1 pt-1 border-t border-base-200 text-[9px] text-success font-mono truncate">
                ← {{ item.response }}
              </div>
            </div>
            <div v-if="history.length === 0" class="text-center opacity-20 mt-20 text-xs italic">NO RECENT COMMANDS</div>
          </div>
        </div>
      </aside>
    </main>

    <!-- Footer Stats -->
    <footer class="h-6 bg-base-100 border-t border-base-200 px-4 flex items-center justify-between text-[10px] opacity-50 font-medium">
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1"><CpuIcon :size="10" /> PN532 HSU</span>
        <span class="flex items-center gap-1"><ActivityIcon :size="10" /> {{ filteredLogs.length }} Messages</span>
      </div>
      <div>
        <span>Built with ☕ and CarrotRFID</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick, reactive } from 'vue'
import { 
  Terminal as TerminalIcon, 
  Cpu as CpuIcon, 
  Settings as SettingsIcon, 
  Zap as ZapIcon,
  CreditCard as CreditCardIcon,
  Scan as ScanIcon,
  RotateCcw as RotateCcwIcon,
  ArrowUpRight as ArrowUpRightIcon,
  Activity as ActivityIcon,
  Search as SearchIcon
} from 'lucide-vue-next'

// --- State Definitions ---
const isConnected = ref(false)
const cmdHex = ref('')
const loading = reactive({ connect: false, send: false })
const logs = ref([])
const history = ref([])
const activeFilters = ref(['DRIVER', 'PROTOCOL', 'DEBUG', 'INFO', 'WARN', 'ERROR'])
const logViewport = ref(null)
const monitorTab = ref('logs')
const autoScan = ref(false)
const txCrc = ref(true)
const rxCrc = ref(true)

const options = reactive({ ports: [], readers: [], baudrates: [] })
const config = reactive({ port: '', baudrate: 115200, reader_type: 'PN532_HSU' })
const target = reactive({ uid: null, sak: null, type: null })

const categories = ref([])
const activeCategory = ref('')
const presets = ref([])

// --- Computed ---
const filteredLogs = computed(() => logs.value.filter(l => activeFilters.value.includes(l.level)))

// --- Logic ---
const fetchOptions = async () => {
  try {
    const res = await fetch('/api/hardware/options')
    const data = await res.json()
    Object.assign(options, data)
    if (!config.port && options.ports.length > 0) config.port = options.ports[0]
  } catch (e) {}
}

const refreshPorts = async () => {
  await fetchOptions()
}

const fetchCategories = async () => {
  try {
    const res = await fetch('/api/presets')
    categories.value = await res.json()
    if (categories.value.length > 0) activeCategory.value = categories.value[0]
  } catch (e) {}
}

const fetchPresets = async (category: string) => {
  if (!category) return
  try {
    const res = await fetch(`/api/presets/${category}`)
    presets.value = await res.json()
  } catch (e) {}
}

const fetchTarget = async () => {
  if (!isConnected.value) return
  try {
    const res = await fetch('/api/hardware/target')
    const data = await res.json()
    Object.assign(target, data)
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
  } catch (e) { isConnected.value = false }
}

const updateConfig = async () => {
  if (!isConnected.value) return
  await fetch('/api/hardware/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tx_crc: txCrc.value, rx_crc: rxCrc.value })
  })
}

const connectHardware = async () => {
  loading.connect = true
  try {
    const res = await fetch('/api/hardware/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    })
    if (res.ok) {
      isConnected.value = true
      await updateConfig()
    } else {
      const err = await res.json()
      alert(err.detail || 'Connection failed')
    }
  } catch (e) { alert('Network error') }
  finally { loading.connect = false }
}

const disconnectHardware = async () => {
  await fetch('/api/hardware/disconnect', { method: 'POST' })
  isConnected.value = false
  target.uid = null
}

const sendCmd = async () => {
  if (!cmdHex.value || loading.send) return
  loading.send = true
  try {
    const res = await fetch('/api/cmd/transceive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hex: cmdHex.value })
    })
    const data = await res.json()
    if (res.ok) {
      history.value.unshift({ 
        hex: cmdHex.value, 
        response: data.response, 
        timestamp: new Date().toISOString() 
      })
      if (history.value.length > 50) history.value.pop()
    } else {
      alert(data.detail || 'Command failed')
    }
  } catch (e) { alert('Network error') }
  finally { loading.send = false }
}

const injectPreset = (item: any) => {
  cmdHex.value = item.hex
}

// --- Utils ---
const toggleFilter = (l: string) => {
  const i = activeFilters.value.indexOf(l)
  i > -1 ? activeFilters.value.splice(i, 1) : activeFilters.value.push(l)
}

const clearLogs = () => logs.value = []

const formatTime = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
}

const levelClass = (l: string) => {
  switch(l) {
    case 'ERROR': return 'text-error font-bold'
    case 'WARN': return 'text-warning font-bold'
    case 'INFO': return 'text-info font-bold'
    case 'DRIVER': return 'text-secondary font-bold'
    case 'PROTOCOL': return 'text-primary font-bold'
    default: return 'text-neutral-content'
  }
}

const levelTextClass = (l: string) => {
  switch(l) {
    case 'ERROR': return 'text-error'
    case 'WARN': return 'text-warning'
    case 'INFO': return 'text-info'
    case 'DRIVER': return 'text-secondary'
    case 'PROTOCOL': return 'text-primary'
    default: return 'text-neutral-content opacity-70'
  }
}

// --- Watchers ---
watch(activeCategory, (newCat) => fetchPresets(newCat))

watch(filteredLogs, () => {
  nextTick(() => {
    if (logViewport.value) logViewport.value.scrollTop = logViewport.value.scrollHeight
  })
}, { deep: true })

// --- Lifecycle ---
onMounted(() => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/logs`)
  ws.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data)
      logs.value.push(d)
      if (logs.value.length > 1000) logs.value.shift()
    } catch(err) {}
  }

  fetchOptions()
  fetchCategories()
  checkStatus()
  setInterval(checkStatus, 3000)
  
  // Auto scan interval
  setInterval(() => {
    if (autoScan.value && isConnected.value) fetchTarget()
  }, 2000)
})
</script>

<style>
/* Modern Scrollbars */
::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

/* Glassmorphism */
.card {
  background-color: hsl(var(--b1) / 0.7);
  backdrop-filter: blur(8px);
}

.tab-active {
  color: hsl(var(--p)) !important;
  border-bottom: 2px solid hsl(var(--p)) !important;
}

/* 渐变背景效果 */
.bg-base-100 {
  background-color: hsl(var(--b1) / 0.8);
  backdrop-filter: blur(12px);
}
</style>
