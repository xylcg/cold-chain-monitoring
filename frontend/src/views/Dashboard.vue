<template>
  <div class="dashboard">
    <div class="page-header">
      <h2 class="page-title">全局态势图</h2>
      <div class="header-meta">
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span>实时监控中</span>
        </div>
        <span class="update-time">更新间隔 10s</span>
      </div>
    </div>

    <!-- KPI 卡片 -->
    <div class="kpi-grid">
      <div class="kpi-card kpi-card--blue">
        <div class="kpi-icon-box blue">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">设备在线</div>
          <div class="kpi-value">
            <span class="kpi-number">{{ store.kpi.online_devices }}</span>
            <span class="kpi-unit">/ {{ store.kpi.total_devices }}</span>
          </div>
          <div class="kpi-bar">
            <div class="kpi-fill blue-fill" :style="{ width: store.kpi.online_rate + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--green">
        <div class="kpi-icon-box green">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">温控达标率</div>
          <div class="kpi-value">
            <span class="kpi-number" :class="store.kpi.temperature_compliance_rate >= 95 ? 'text-teal' : 'text-amber'">
              {{ store.kpi.temperature_compliance_rate }}
            </span>
            <span class="kpi-unit">%</span>
          </div>
          <div class="kpi-bar">
            <div class="kpi-fill green-fill" :style="{ width: store.kpi.temperature_compliance_rate + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--red" v-if="store.kpi.active_alerts > 0">
        <div class="kpi-icon-box red">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">活跃告警</div>
          <div class="kpi-value">
            <span class="kpi-number text-red">{{ store.kpi.active_alerts }}</span>
            <span class="kpi-unit">条</span>
          </div>
          <span class="kpi-tag tag-red">需处理</span>
        </div>
      </div>

      <div class="kpi-card kpi-card--clean" v-else>
        <div class="kpi-icon-box green">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">活跃告警</div>
          <div class="kpi-value">
            <span class="kpi-number text-teal">0</span>
            <span class="kpi-unit">条</span>
          </div>
          <span class="kpi-tag tag-teal">全部正常</span>
        </div>
      </div>

      <div class="kpi-card kpi-card--dual">
        <div class="kpi-dual">
          <div class="kpi-half">
            <div class="kpi-label">平均温度</div>
            <div class="kpi-value-sm">
              <span class="kpi-number-sm">{{ store.kpi.avg_temperature }}</span>
              <span class="kpi-unit-sm">°C</span>
            </div>
          </div>
          <div class="kpi-v-divider"></div>
          <div class="kpi-half">
            <div class="kpi-label">平均湿度</div>
            <div class="kpi-value-sm">
              <span class="kpi-number-sm">{{ store.kpi.avg_humidity }}</span>
              <span class="kpi-unit-sm">%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 设备实时状态 -->
    <div class="glass-card">
      <div class="card-header-row">
        <div>
          <h3>设备实时状态</h3>
          <span class="card-sub">共 {{ store.devices.length }} 台设备在线监控</span>
        </div>
        <div class="legend-row">
          <span class="legend-it"><span class="legend-dot green-dot"></span>正常</span>
          <span class="legend-it"><span class="legend-dot amber-dot"></span>预警</span>
          <span class="legend-it"><span class="legend-dot red-dot"></span>告警</span>
        </div>
      </div>
      <div class="table-box">
        <el-table :data="store.devices" stripe style="width: 100%" :max-height="400">
          <el-table-column prop="device_id" label="设备 ID" width="130">
            <template #default="{ row }">
              <code class="cell-id">{{ row.device_id }}</code>
            </template>
          </el-table-column>
          <el-table-column prop="device_type" label="类型" width="80">
            <template #default="{ row }">
              <span class="type-tag" :class="row.device_type">
                {{ row.device_type === 'vehicle' ? '车辆' : '冷库' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="temperature" label="温度" width="90" sortable>
            <template #default="{ row }">
              <span class="temp-val" :class="getTempClass(row.temperature)">{{ row.temperature }}°C</span>
            </template>
          </el-table-column>
          <el-table-column prop="humidity" label="湿度" width="80" />
          <el-table-column prop="door_status" label="车门" width="80">
            <template #default="{ row }">
              <span class="door-badge" :class="{ open: row.door_status }">
                {{ row.door_status ? '开启' : '关闭' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="active_alerts" label="告警" width="70">
            <template #default="{ row }">
              <span v-if="row.active_alerts > 0" class="alert-badge">{{ row.active_alerts }}</span>
              <span v-else class="none-text">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="last_update" label="最后更新" min-width="150">
            <template #default="{ row }">
              <span class="time-text">{{ row.last_update }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { getTempClass } from '@/utils'

const store = useAppStore()
</script>

<style scoped>
.dashboard { animation: fadeInUp 0.45s ease-out; }

.header-meta { display: flex; align-items: center; gap: 14px; }
.live-indicator {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--teal); font-family: var(--font-mono); font-weight: 500;
}
.live-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--teal);
  animation: pulse-ring 2s ease-out infinite;
}
.update-time {
  font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);
  background: var(--bg-input); padding: 3px 10px; border-radius: 20px;
}

/* --- KPI --- */
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 0.8fr;
  gap: 14px;
  margin-bottom: 22px;
}
.kpi-card {
  background: var(--bg-card);
  backdrop-filter: var(--blur-card);
  -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  display: flex; gap: 14px;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
}
.kpi-card:hover { box-shadow: var(--shadow); transform: translateY(-2px); }
.kpi-card--red { border-color: rgba(239,68,68,0.2); }

.kpi-icon-box {
  width: 44px; height: 44px; border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.kpi-icon-box.blue { background: var(--accent-bg); color: var(--accent); }
.kpi-icon-box.green { background: var(--teal-bg); color: var(--teal); }
.kpi-icon-box.red { background: var(--red-bg); color: var(--red); }

.kpi-body { flex: 1; min-width: 0; }
.kpi-label { font-size: 11px; color: var(--text-muted); letter-spacing: 0.03em; margin-bottom: 4px; }
.kpi-value { display: flex; align-items: baseline; gap: 3px; margin-bottom: 8px; }
.kpi-number { font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--text-title); line-height: 1; }
.kpi-unit { font-size: 12px; color: var(--text-muted); font-family: var(--font-body); }
.text-teal { color: var(--teal) !important; }
.text-amber { color: var(--amber) !important; }
.text-red { color: var(--red) !important; }


.kpi-bar { height: 3px; background: var(--bg-input); border-radius: 3px; overflow: hidden; }
.kpi-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
.blue-fill { background: linear-gradient(90deg, var(--accent), var(--accent-light)); }
.green-fill { background: linear-gradient(90deg, var(--teal), var(--teal-light)); }

.kpi-tag {
  display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px;
  font-family: var(--font-mono); letter-spacing: 0.04em; text-transform: uppercase;
}
.tag-red { background: var(--red-bg); color: var(--red); }
.tag-teal { background: var(--teal-bg); color: var(--teal); }

/* Dual KPI */
.kpi-dual { display: flex; align-items: center; width: 100%; }
.kpi-half { flex: 1; text-align: center; }
.kpi-v-divider { width: 1px; height: 32px; background: var(--border-light); }
.kpi-value-sm { display: flex; align-items: baseline; justify-content: center; gap: 2px; }
.kpi-number-sm { font-family: var(--font-display); font-size: 24px; font-weight: 800; color: var(--text-title); }
.kpi-unit-sm { font-size: 11px; color: var(--text-muted); }

/* Table */
.card-header-row {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
}
.card-header-row h3 { font-size: 15px; font-weight: 700; color: var(--text-title); }
.card-sub { font-size: 12px; color: var(--text-muted); margin-left: 8px; }
.legend-row { display: flex; gap: 16px; align-items: center; }
.legend-it { font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; }
.legend-dot { width: 6px; height: 6px; border-radius: 50%; }
.green-dot { background: var(--teal); }
.amber-dot { background: var(--amber); }
.red-dot { background: var(--red); }

.table-box { overflow-x: auto; }
.cell-id {
  font-family: var(--font-mono); font-size: 11px; color: var(--accent);
  background: var(--accent-bg); padding: 2px 8px; border-radius: 4px; font-weight: 500;
}
.type-tag {
  font-size: 11px; padding: 2px 8px; border-radius: 20px; font-weight: 600;
}
.type-tag.vehicle { background: var(--accent-bg); color: var(--accent); }
.type-tag.cold_room { background: var(--teal-bg); color: var(--teal); }
.temp-val { font-family: var(--font-mono); font-weight: 600; font-size: 13px; }
.door-badge { font-size: 11px; padding: 2px 8px; border-radius: 12px; background: var(--bg-input); color: var(--text-secondary); }
.door-badge.open { background: var(--amber-bg); color: var(--amber); }
.alert-badge {
  font-family: var(--font-mono); font-size: 11px; font-weight: 700;
  background: var(--red); color: #fff; padding: 2px 7px; border-radius: 10px;
}
.none-text { color: var(--teal); font-weight: 600; }
.time-text { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }

@media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
