<template>
  <div class="device-monitor">
    <div class="page-header">
      <h2 class="page-title">设备监控</h2>
      <div class="header-right">
        <el-input v-model="searchText" placeholder="搜索设备 ID..." size="default" style="width: 220px" clearable>
          <template #prefix>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </template>
        </el-input>
        <el-select v-model="filterType" placeholder="全部类型" style="width: 120px" clearable>
          <el-option label="全部" value="" />
          <el-option label="车辆" value="vehicle" />
          <el-option label="冷库" value="cold_room" />
        </el-select>
        <div class="dev-count">
          <span class="count-num">{{ filteredDevices.length }}</span>
          <span class="count-lbl">台设备</span>
        </div>
      </div>
    </div>

    <div class="card-grid">
      <div v-for="device in filteredDevices" :key="device.device_id"
        class="dev-card" :class="{ 'is-alert': device.active_alerts > 0 }"
        @click="selectDevice(device)">
        <div class="card-head">
          <div class="head-left">
            <code class="dev-id">{{ device.device_id }}</code>
            <span class="dev-type" :class="device.device_type">
              {{ device.device_type === 'vehicle' ? '冷藏车' : '冷库' }}
            </span>
          </div>
          <span class="status-dot" :class="device.online ? 'online' : 'offline'"></span>
        </div>

        <div class="temp-block">
          <div class="temp-num" :class="getTempClass(device.temperature)">
            {{ device.temperature }}<small>°C</small>
          </div>
          <div class="temp-msg" :class="getTempClass(device.temperature)">
            {{ getTempStatus(device.temperature) }}
          </div>
        </div>

        <div class="metrics">
          <div class="met">
            <span class="met-l">湿度</span>
            <span class="met-v">{{ device.humidity }}%</span>
          </div>
          <div class="met">
            <span class="met-l">车门</span>
            <span class="met-v" :class="{ warn: device.door_status }">{{ device.door_status ? '开启' : '关闭' }}</span>
          </div>
          <div class="met">
            <span class="met-l">告警</span>
            <span class="met-v" :class="{ danger: device.active_alerts > 0 }">{{ device.active_alerts || 0 }}</span>
          </div>
        </div>

        <div class="card-foot">
          <span class="foot-status" :class="{ off: !device.online }">{{ device.online ? '在线' : '离线' }}</span>
          <span class="foot-time">{{ formatTime(device.last_update) }}</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="showDetail" :title="selected?.device_id + ' · 设备详情'" width="480px" class="custom-dialog">
      <div v-if="selected" class="detail">
        <div class="detail-grid">
          <div class="d-item"><span class="d-lab">类型</span><span class="d-val">{{ selected.device_type === 'vehicle' ? '冷藏车' : '冷库' }}</span></div>
          <div class="d-item"><span class="d-lab">温度</span><span class="d-val highlight" :class="getTempClass(selected.temperature)">{{ selected.temperature }}°C</span></div>
          <div class="d-item"><span class="d-lab">湿度</span><span class="d-val">{{ selected.humidity }}%</span></div>
          <div class="d-item"><span class="d-lab">车门</span><span class="d-val">{{ selected.door_status ? '开启' : '关闭' }}</span></div>
          <div class="d-item"><span class="d-lab">振动</span><span class="d-val">{{ selected.vibration || '—' }}</span></div>
          <div class="d-item"><span class="d-lab">告警</span><span class="d-val" :class="{ danger: selected.active_alerts > 0 }">{{ selected.active_alerts || 0 }}</span></div>
        </div>
        <div class="d-time"><span class="d-lab">最后更新</span><span class="d-val mono">{{ formatTime(selected.last_update) }}</span></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { getTempClass, formatTime } from '@/utils'

const store = useAppStore()
const searchText = ref('')
const filterType = ref('')
const showDetail = ref(false)
const selected = ref<any>(null)

const filteredDevices = computed(() => {
  let list = store.devices
  if (searchText.value) list = list.filter((d: any) => d.device_id.toLowerCase().includes(searchText.value.toLowerCase()))
  if (filterType.value) list = list.filter((d: any) => d.device_type === filterType.value)
  return list
})

function getTempStatus(temp: number) {
  if (temp > 8) return '温度偏高'
  if (temp > 6) return '接近预警'
  if (temp < -25) return '温度过低'
  return '正常范围'
}

function selectDevice(device: any) { selected.value = device; showDetail.value = true }
</script>

<style scoped>
.device-monitor { animation: fadeInUp 0.45s ease-out; }

.header-right { display: flex; align-items: center; gap: 10px; }
.dev-count { display: flex; align-items: baseline; gap: 4px; padding-left: 12px; border-left: 1px solid var(--border-light); }
.count-num { font-family: var(--font-display); font-size: 20px; font-weight: 800; color: var(--accent); }
.count-lbl { font-size: 12px; color: var(--text-muted); }

/* Grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.dev-card {
  background: var(--bg-card);
  backdrop-filter: var(--blur-card);
  -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
}
.dev-card:hover {
  box-shadow: var(--shadow); transform: translateY(-2px); border-color: var(--border-focus);
}
.dev-card.is-alert {
  border-color: rgba(239,68,68,0.2);
  box-shadow: 0 0 20px rgba(239,68,68,0.06);
}

.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.head-left { display: flex; align-items: center; gap: 8px; }
.dev-id {
  font-family: var(--font-mono); font-size: 11px; color: var(--accent);
  background: var(--accent-bg); padding: 2px 8px; border-radius: 4px; font-weight: 500;
}
.dev-type {
  font-size: 10px; padding: 2px 7px; border-radius: 20px; font-weight: 600;
}
.dev-type.vehicle { background: var(--accent-bg); color: var(--accent); }
.dev-type.cold_room { background: var(--teal-bg); color: var(--teal); }

.temp-block {
  text-align: center; padding: 14px 0; margin-bottom: 12px;
  background: rgba(0,0,0,0.02); border-radius: var(--radius);
}
.temp-num { font-family: var(--font-display); font-size: 44px; font-weight: 800; color: var(--text-title); line-height: 1; }
.temp-num small { font-size: 16px; font-weight: 500; }
.temp-msg { font-size: 10px; font-weight: 600; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.04em; }
.temp-normal .temp-msg, .temp-normal { color: var(--teal); }
.temp-warn .temp-msg, .temp-warn { color: var(--amber); }
.temp-danger .temp-msg, .temp-danger { color: var(--red); }
.temp-normal .temp-num { color: var(--teal); }
.temp-warn .temp-num { color: var(--amber); }
.temp-danger .temp-num { color: var(--red); }

.metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; }
.met { text-align: center; }
.met-l { display: block; font-size: 10px; color: var(--text-muted); letter-spacing: 0.03em; margin-bottom: 2px; }
.met-v { font-size: 13px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); }
.met-v.warn { color: var(--amber); }
.met-v.danger { color: var(--red); }

.card-foot { display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid var(--border-light); }
.foot-status { font-size: 11px; color: var(--teal); font-weight: 600; }
.foot-status.off { color: var(--text-muted); }
.foot-time { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }

/* Detail dialog */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.d-item { padding: 12px; background: var(--bg-input); border-radius: var(--radius); display: flex; flex-direction: column; gap: 4px; }
.d-lab { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.d-val { font-size: 15px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); }
.d-val.highlight { font-family: var(--font-display); font-size: 18px; }
.d-val.danger { color: var(--red) !important; }
.d-time { margin-top: 10px; padding: 12px; background: var(--bg-input); border-radius: var(--radius); display: flex; justify-content: space-between; align-items: center; }
.mono { font-family: var(--font-mono); color: var(--text-secondary); }

@media (max-width: 768px) { .detail-grid { grid-template-columns: 1fr; } }
</style>
