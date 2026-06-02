<template>
  <div class="alert-center">
    <div class="page-header">
      <h2 class="page-title">告警中心</h2>
      <div class="header-stats">
        <span class="stat-badge" :class="store.kpi.active_alerts > 0 ? 'has-alerts' : 'clean'">
          {{ store.kpi.active_alerts > 0 ? `⚠ ${store.kpi.active_alerts} 条活跃告警` : '✓ 全部正常' }}
        </span>
      </div>
    </div>

    <div v-if="store.activeAlerts.length === 0" class="empty-block">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="1.5" stroke-linecap="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="8 12 11 15 16 9"/>
      </svg>
      <p>当前无活跃告警</p>
      <span>所有设备运行正常，温控指标在安全范围内</span>
    </div>

    <div v-else class="alert-grid">
      <div v-for="device in store.activeAlerts" :key="device.device_id" class="alert-card">
        <div class="card-top">
          <div class="top-left">
            <code class="aid">{{ device.device_id }}</code>
            <span class="acount" :class="device.active_alerts > 3 ? 'critical' : 'warning'">
              {{ device.active_alerts }} 条告警
            </span>
          </div>
          <div class="atemp" :class="getTempClass(device.last_temperature)">
            <span class="atemp-num">{{ device.last_temperature }}</span>
            <span class="atemp-u">°C</span>
          </div>
        </div>
        <div class="card-bottom">
          <span class="atime">
            <span class="atime-dot"></span>
            {{ formatTime(device.last_update) }}
          </span>
          <span class="adetail">查看详情 →</span>
        </div>
      </div>
    </div>

    <div class="glass-card">
      <h3 class="sec-title">告警级别说明</h3>
      <div class="sev-list">
        <div class="sev-item">
          <span class="sev-badge amber">一般</span>
          <span>推送至配送员终端，需现场确认处置</span>
        </div>
        <div class="sev-item">
          <span class="sev-badge red">严重</span>
          <span>通知区域经理和维修团队立即响应</span>
        </div>
        <div class="sev-item">
          <span class="sev-badge crit">紧急</span>
          <span>启动应急预案，通知客户（如疫苗温度失控）</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { getTempClass, formatTime } from '@/utils'
const store = useAppStore()
</script>

<style scoped>
.alert-center { animation: fadeInUp 0.45s ease-out; }

.stat-badge {
  font-family: var(--font-mono); font-size: 13px; font-weight: 600;
  padding: 6px 14px; border-radius: 20px;
}
.stat-badge.has-alerts { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239,68,68,0.15); }
.stat-badge.clean { color: var(--teal); background: var(--teal-bg); border: 1px solid rgba(0,210,160,0.12); }

.empty-block {
  text-align: center; padding: 60px 0; color: var(--text-muted);
}
.empty-block p { font-size: 15px; font-weight: 500; margin: 10px 0 4px; color: var(--text-secondary); }
.empty-block span { font-size: 12px; }

.alert-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px; margin-bottom: 24px;
}

.alert-card {
  background: var(--bg-card); backdrop-filter: var(--blur-card); -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid rgba(239,68,68,0.18); border-radius: var(--radius-lg);
  padding: 18px; box-shadow: var(--shadow-sm); transition: all 0.3s ease;
}
.alert-card:hover {
  border-color: rgba(239,68,68,0.35); box-shadow: 0 0 20px rgba(239,68,68,0.08); transform: translateY(-2px);
}

.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.top-left { display: flex; align-items: center; gap: 10px; }
.aid {
  font-family: var(--font-mono); font-size: 12px; color: var(--accent);
  background: var(--accent-bg); padding: 3px 8px; border-radius: 4px; font-weight: 500;
}
.acount { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-family: var(--font-mono); }
.acount.warning { color: var(--amber); background: var(--amber-bg); border: 1px solid rgba(245,158,11,0.12); }
.acount.critical { color: #fff; background: var(--red); }

.atemp { display: flex; align-items: baseline; gap: 2px; }
.atemp-num { font-family: var(--font-display); font-size: 30px; font-weight: 800; line-height: 1; }
.atemp-u { font-size: 12px; opacity: 0.7; }
.temp-normal { color: var(--teal); }
.temp-warn { color: var(--amber); }
.temp-danger { color: var(--red); }

.card-bottom { display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-light); }
.atime { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }
.atime-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--red); animation: pulse-ring 1.5s ease-in-out infinite; }
.adetail { font-size: 11px; color: var(--accent); font-family: var(--font-mono); cursor: pointer; }

.sec-title { font-size: 15px; font-weight: 700; color: var(--text-title); margin-bottom: 14px; }

.sev-list { display: flex; flex-direction: column; gap: 10px; }
.sev-item {
  display: flex; align-items: center; gap: 14px; padding: 12px 14px;
  background: var(--bg-input); border-radius: var(--radius);
  font-size: 13px; color: var(--text-secondary);
}
.sev-badge {
  font-size: 11px; font-weight: 700; padding: 3px 12px; border-radius: 4px;
  font-family: var(--font-mono); letter-spacing: 0.04em; flex-shrink: 0;
}
.sev-badge.amber { color: var(--amber); background: var(--amber-bg); border: 1px solid rgba(245,158,11,0.15); }
.sev-badge.red { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239,68,68,0.15); }
.sev-badge.crit { color: #fff; background: var(--red); }
</style>
