<template>
  <div class="h-screen flex flex-col bg-base-300 p-4 gap-4 overflow-hidden" data-theme="dark">
    <!-- 头部导航 -->
    <div class="navbar bg-base-100 rounded-box shadow-lg px-6">
      <div class="flex-1">
        <a class="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          CarrotRFID Web Console
        </a>
      </div>
      <div class="flex-none gap-4">
        <div class="stats bg-base-200 shadow scale-90">
          <div class="stat py-2 px-4">
            <div class="stat-title">Hardware Status</div>
            <div class="stat-value text-sm flex items-center gap-2" :class="isConnected ? 'text-success' : 'text-error'">
              <div class="badge badge-xs" :class="isConnected ? 'badge-success' : 'badge-error'"></div>
              {{ isConnected ? 'CONNECTED' : 'DISCONNECTED' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="flex-1 flex flex-col gap-4 min-h-0">
      <!-- 日志面板 -->
      <div class="flex-1 flex flex-col bg-base-100 rounded-box shadow-lg border border-base-200 overflow-hidden">
        <div class="p-4 border-b border-base-200 flex justify-between items-center">
          <h2 class="font-bold flex items-center gap-2">
            <TerminalIcon :size="18" /> Real-time Logs
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
        
        <div class="flex-1 overflow-y-auto p-4 mockup-code bg-neutral text-neutral-content rounded-none m-0" ref="logViewport">
          <pre v-for="(log, index) in filteredLogs" :key="index" :data-prefix="'>'" :class="levelTextClass(log.level)">
            <code><span class="opacity-50 text-xs">[{{ formatTime(log.timestamp) }}]</span> <span class="font-bold">[{{ log.level }}]</span> {{ log.message }}</code>
          </pre>
          <div v-if="filteredLogs.length === 0" class="text-center opacity-20 mt-10 italic">Waiting for logs...</div>
        </div>
      </div>

      <!-- 指令面板 -->
      <div class="bg-base-100 rounded-box shadow-lg p-6 border border-base-200">
        <div class="flex flex-col gap-4">
          <h2 class="font-bold flex items-center gap-2">
            <CpuIcon :size="18" /> Command Debugger
          </h2>
          <div class="join w-full">
            <input 
              v-model="cmdHex" 
              type="text" 
              placeholder="Enter Hex Command (e.g. 00 00 FF 03 FD D4 14 01 17 00)" 
              class="input input-bordered join-item flex-1 font-mono"
              @keyup.enter="sendCmd"
            />
            <button 
              class="btn btn-primary join-item px-8" 
              :disabled="!isConnected || loading"
              @click="sendCmd"
            >
              <span v-if="loading" class="loading loading-spinner loading-xs"></span>
              SEND
            </button>
          </div>
          <div v-if="lastResponse" class="collapse collapse-arrow bg-base-200 border border-base-300">
            <input type="checkbox" checked /> 
            <div class="collapse-title text-sm font-medium opacity-70">
              Last Response
            </div>
            <div class="collapse-content"> 
              <div class="bg-black p-3 rounded font-mono text-primary break-all">
                {{ lastResponse }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { Terminal as TerminalIcon, Cpu as CpuIcon } from 'lucide-vue-next'

const isConnected = ref(false)
const cmdHex = ref('')
const lastResponse = ref('')
const loading = ref(false)
const logs = ref([])
const activeFilters = ref(['DEBUG', 'INFO', 'WARN', 'ERROR'])
const logViewport = ref(null)

const filteredLogs = computed(() => {
  return logs.value.filter(log => activeFilters.value.includes(log.level))
})

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

const toggleFilter = (level) => {
  const index = activeFilters.value.indexOf(level)
  if (index > -1) activeFilters.value.splice(index, 1)
  else activeFilters.value.push(level)
}

const clearLogs = () => logs.value = []

const formatTime = (isoStr) => {
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

const connectWS = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/logs`)

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      logs.value.push(data)
      if (logs.value.length > 500) logs.value.shift()
    } catch(e) {}
  }

  ws.onclose = () => setTimeout(connectWS, 2000)
}

const checkStatus = async () => {
  try {
    const res = await fetch('/api/status')
    const data = await res.json()
    isConnected.value = data.connected
  } catch (e) {
    isConnected.value = false
  }
}

const sendCmd = async () => {
  if (!cmdHex.value || loading.value) return
  loading.value = true
  try {
    const res = await fetch('/api/cmd', {
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
    loading.value = false
  }
}

onMounted(() => {
  connectWS()
  checkStatus()
  setInterval(checkStatus, 5000)
})
</script>

<style>
/* 隐藏滚动条但保留滚动功能 */
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
</style>
