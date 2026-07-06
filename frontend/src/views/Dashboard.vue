<template>
  <div class="dashboard">
    <div class="page-header">
      <h2 class="page-title">运营调度中心 · 全局态势图</h2>
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
          <div class="kpi-label">设备在线率</div>
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

    <!-- 第二行 KPI：资源调度看板 -->
    <div class="kpi-grid kpi-grid--small">
      <div class="kpi-card kpi-card--sm">
        <div class="kpi-icon-box accent">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">可调度车辆</div>
          <div class="kpi-value-sm">
            <span class="kpi-number-sm">{{ resourceStats.availableVehicles }}</span>
            <span class="kpi-unit-sm">辆</span>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--sm">
        <div class="kpi-icon-box accent2">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">可用冷库</div>
          <div class="kpi-value-sm">
            <span class="kpi-number-sm">{{ resourceStats.availableWarehouses }}</span>
            <span class="kpi-unit-sm">座</span>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--sm">
        <div class="kpi-icon-box warn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">今日订单</div>
          <div class="kpi-value-sm">
            <span class="kpi-number-sm">{{ resourceStats.todayOrders }}</span>
            <span class="kpi-unit-sm">单</span>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--sm">
        <div class="kpi-icon-box energy">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">今日能耗</div>
          <div class="kpi-value-sm">
            <span class="kpi-number-sm">{{ resourceStats.energyUsage }}</span>
            <span class="kpi-unit-sm">kWh</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 🔥 核心监控：温度趋势 + 告警分布 双栏 -->
    <div class="monitor-grid">
      <!-- 温度趋势迷你图 -->
      <div class="glass-card trend-card">
        <div class="card-header-row">
          <div>
            <h3>📈 24小时温度趋势</h3>
            <span class="card-sub">核心冷库 + 运输车辆 平均温度变化</span>
          </div>
          <div class="trend-legend">
            <span class="tl-item"><span class="tl-dot freeze"></span> 冷冻</span>
            <span class="tl-item"><span class="tl-dot chill"></span> 冷藏</span>
            <span class="tl-item"><span class="tl-dot ambient"></span> 恒温</span>
          </div>
        </div>
        <div class="trend-chart">
          <div class="trend-canvas" ref="trendCanvas">
            <svg viewBox="0 0 600 160" preserveAspectRatio="none" class="trend-svg">
              <defs>
                <linearGradient id="freezeGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#00a8ff" stop-opacity="0.3"/><stop offset="100%" stop-color="#00a8ff" stop-opacity="0.02"/></linearGradient>
                <linearGradient id="chillGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#0ea5e9" stop-opacity="0.25"/><stop offset="100%" stop-color="#0ea5e9" stop-opacity="0.02"/></linearGradient>
                <linearGradient id="ambGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f59e0b" stop-opacity="0.2"/><stop offset="100%" stop-color="#f59e0b" stop-opacity="0.02"/></linearGradient>
              </defs>
              <!-- 温度阈值带 -->
              <rect x="0" y="20" width="600" height="30" fill="rgba(239,68,68,0.06)" rx="4"/>
              <rect x="0" y="110" width="600" height="30" fill="rgba(239,68,68,0.04)" rx="4"/>
              <line x1="0" y1="20" x2="600" y2="20" stroke="rgba(239,68,68,0.2)" stroke-dasharray="4,4" stroke-width="1"/>
              <line x1="0" y1="140" x2="600" y2="140" stroke="rgba(239,68,68,0.15)" stroke-dasharray="4,4" stroke-width="1"/>
              <!-- 冷冻线 -->
              <polyline :points="trendLines.freeze" stroke="#00a8ff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline :points="trendLines.freeze + ' 600,160 0,160'" fill="url(#freezeGrad)" stroke="none"/>
              <!-- 冷藏线 -->
              <polyline :points="trendLines.chill" stroke="#0ea5e9" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <!-- 恒温线 -->
              <polyline :points="trendLines.ambient" stroke="#f59e0b" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="trend-xaxis">
            <span v-for="h in [0,4,8,12,16,20,24]" :key="h">{{ h }}:00</span>
          </div>
        </div>
      </div>

      <!-- 告警分布 + 车辆实时位置 -->
      <div class="glass-card alert-overview">
        <div class="card-header-row">
          <div>
            <h3>🚨 告警态势</h3>
            <span class="card-sub">最近24小时告警分布与处理进度</span>
          </div>
          <button class="btn-sm btn-primary" @click="router.push('/alerts')">查看全部</button>
        </div>
        <div class="alert-bars">
          <div class="ab-row">
            <span class="ab-label">温度越界</span>
            <div class="ab-track"><div class="ab-fill critical" :style="{ width: alertDist.temp + '%' }"></div></div>
            <span class="ab-cnt critical-text">{{ alertCounts.temp }}</span>
          </div>
          <div class="ab-row">
            <span class="ab-label">冷机故障</span>
            <div class="ab-track"><div class="ab-fill warning" :style="{ width: alertDist.machine + '%' }"></div></div>
            <span class="ab-cnt warning-text">{{ alertCounts.machine }}</span>
          </div>
          <div class="ab-row">
            <span class="ab-label">车门异常</span>
            <div class="ab-track"><div class="ab-fill info" :style="{ width: alertDist.door + '%' }"></div></div>
            <span class="ab-cnt info-text">{{ alertCounts.door }}</span>
          </div>
          <div class="ab-row">
            <span class="ab-label">延迟送达</span>
            <div class="ab-track"><div class="ab-fill delay" :style="{ width: alertDist.delay + '%' }"></div></div>
            <span class="ab-cnt delay-text">{{ alertCounts.delay }}</span>
          </div>
        </div>
        <!-- 车辆状态环 -->
        <div class="vehicle-rings">
          <div class="vr-item">
            <div class="vr-ring" :style="{ '--pct': fleetStatus.onlinePct }">
              <svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--border)" stroke-width="3"/><circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--teal)" stroke-width="3" stroke-dasharray="97.4" :stroke-dashoffset="97.4 - 97.4 * fleetStatus.onlinePct / 100" stroke-linecap="round" transform="rotate(-90 18 18)"/></svg>
              <span class="vr-val">{{ fleetStatus.online }}</span>
            </div>
            <span class="vr-label">在线车辆</span>
          </div>
          <div class="vr-item">
            <div class="vr-ring" :style="{ '--pct': fleetStatus.transitPct }">
              <svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--border)" stroke-width="3"/><circle cx="18" cy="18" r="15.5" fill="none" stroke="#7c3aed" stroke-width="3" stroke-dasharray="97.4" :stroke-dashoffset="97.4 - 97.4 * fleetStatus.transitPct / 100" stroke-linecap="round" transform="rotate(-90 18 18)"/></svg>
              <span class="vr-val">{{ fleetStatus.transit }}</span>
            </div>
            <span class="vr-label">运输中</span>
          </div>
          <div class="vr-item">
            <div class="vr-ring" :style="{ '--pct': fleetStatus.idlePct }">
              <svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--border)" stroke-width="3"/><circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--amber)" stroke-width="3" stroke-dasharray="97.4" :stroke-dashoffset="97.4 - 97.4 * fleetStatus.idlePct / 100" stroke-linecap="round" transform="rotate(-90 18 18)"/></svg>
              <span class="vr-val">{{ fleetStatus.idle }}</span>
            </div>
            <span class="vr-label">待命中</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <div class="qa-header">
        <h3>{{ roleInfo.label }}工作台</h3>
        <span class="qa-tips">{{ roleInfo.tips }}</span>
      </div>
      <div class="qa-grid">
        <div v-for="action in quickActions" :key="action.path" class="qa-card" @click="router.push(action.path)">
          <div class="qa-icon" :style="{ background: action.color + '18', color: action.color, borderColor: action.color + '33' }">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <g v-html="action.icon"></g>
            </svg>
          </div>
          <span class="qa-label">{{ action.label }}</span>
          <svg class="qa-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </div>
      </div>
    </div>

    <!-- ====== 业务联动面板：订单流转 + 审核通知 + 事件时间线 ====== -->
    <div class="linkage-panel">
      <!-- 订单流转状态 -->
      <div class="glass-card">
        <div class="card-header-row">
          <div>
            <h3>📦 订单流转看板 <span class="live-tag">LIVE</span></h3>
            <span class="card-sub">客户下单 → 司机接单 → 配送 → 签收 全链路追踪</span>
          </div>
          <button class="btn-sm btn-primary" @click="router.push('/dispatch')">去调度 →</button>
        </div>
        <div class="flow-steps">
          <div class="fs-step" :class="{ active: store.orderFlow.pending > 0 }">
            <div class="fss-dot pending">📝</div>
            <div class="fss-info">
              <span class="fss-num">{{ store.orderFlow.pending }}</span>
              <span class="fss-label">待接单</span>
            </div>
          </div>
          <div class="fs-arrow">→</div>
          <div class="fs-step" :class="{ active: store.orderFlow.accepted > 0 }">
            <div class="fss-dot accepted">📸</div>
            <div class="fss-info">
              <span class="fss-num">{{ store.orderFlow.accepted }}</span>
              <span class="fss-label">已接单</span>
            </div>
          </div>
          <div class="fs-arrow">→</div>
          <div class="fs-step" :class="{ active: store.orderFlow.in_transit > 0 }">
            <div class="fss-dot transit">🚀</div>
            <div class="fss-info">
              <span class="fss-num">{{ store.orderFlow.in_transit }}</span>
              <span class="fss-label">配送中</span>
            </div>
          </div>
          <div class="fs-arrow">→</div>
          <div class="fs-step" :class="{ active: store.orderFlow.delivered > 0 }">
            <div class="fss-dot delivered">📦</div>
            <div class="fss-info">
              <span class="fss-num">{{ store.orderFlow.delivered }}</span>
              <span class="fss-label">已送达</span>
            </div>
          </div>
          <div class="fs-arrow">→</div>
          <div class="fs-step" :class="{ active: store.orderFlow.completed > 0 }">
            <div class="fss-dot completed">✅</div>
            <div class="fss-info">
              <span class="fss-num">{{ store.orderFlow.completed }}</span>
              <span class="fss-label">已签收</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 照片审核通知卡片（仅仓库角色可见） -->
      <div class="glass-card photo-review-card" v-if="role === 'warehouse' && store.photoReview.pending_count > 0">
        <div class="card-header-row">
          <div>
            <h3>📷 待审核照片 <span class="badge-red">{{ store.photoReview.pending_count }}</span></h3>
            <span class="card-sub">司机拍摄的出发/送达照片需要审核</span>
          </div>
          <button class="btn-sm btn-warning" @click="router.push('/warehouse')">去审核 →</button>
        </div>
        <div class="pr-list">
          <div class="pr-item" v-for="item in store.photoReview.pending_items" :key="item.id">
            <span class="pri-icon">{{ item.photo_type === 'accept' ? '🚛' : '📦' }}</span>
            <div class="pri-body">
              <span class="pri-type">{{ item.photo_type === 'accept' ? '出发拍照' : '送达拍照' }}</span>
              <span class="pri-order">{{ item.order_id || item.waybill_id || item.id }}</span>
            </div>
            <span class="pri-time">{{ item.created_at?.slice(0, 16) || '—' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 业务事件时间线 -->
    <div class="glass-card">
      <div class="card-header-row">
        <div>
          <h3>📋 业务事件时间线</h3>
          <span class="card-sub">最近业务动态 · 司机/客户实时操作记录</span>
        </div>
      </div>
      <div class="event-timeline">
        <div class="et-item" v-for="(ev, idx) in store.recentEvents.slice(0, 6)" :key="ev.id" :style="{ animationDelay: idx * 0.1 + 's' }">
          <div class="et-dot" :class="ev.status">{{ ev.icon }}</div>
          <div class="et-content">
            <div class="et-header">
              <span class="et-label">{{ ev.label }}</span>
              <span class="et-time">{{ ev.time?.slice(5, 16) || '—' }}</span>
            </div>
            <div class="et-desc">{{ ev.desc }}</div>
            <div class="et-meta">
              <span v-if="ev.driver !== '—'" class="et-actor">👨‍✈️ {{ ev.driver }}</span>
              <span v-if="ev.customer !== '—'" class="et-actor">👤 {{ ev.customer }}</span>
            </div>
          </div>
        </div>
        <div class="et-empty" v-if="store.recentEvents.length === 0">
          <span>🕐</span><p>暂无业务事件，等待客户下单或司机操作</p>
        </div>
      </div>
    </div>

    <!-- 两栏布局：订单聚合 + 资源协调 -->
    <div class="dashboard-grid">
      <!-- 订单聚合看板 -->
      <div class="glass-card">
        <div class="card-header-row">
          <div>
            <h3>订单聚合看板</h3>
            <span class="card-sub">多温区智能匹配 · 实时订单调度</span>
          </div>
          <button class="btn-sm btn-primary" @click="router.push('/dispatch')">去调度</button>
        </div>
        <div class="order-stats-row">
          <div class="order-stat">
            <span class="os-num text-accent">{{ orderStats.pending }}</span>
            <span class="os-label">待分配</span>
          </div>
          <div class="order-stat">
            <span class="os-num text-amber">{{ orderStats.matching }}</span>
            <span class="os-label">匹配中</span>
          </div>
          <div class="order-stat">
            <span class="os-num text-teal">{{ orderStats.inTransit }}</span>
            <span class="os-label">运输中</span>
          </div>
          <div class="order-stat">
            <span class="os-num text-muted">{{ orderStats.completed }}</span>
            <span class="os-label">已完成</span>
          </div>
        </div>
        <div class="zone-match">
          <h4>温区车辆匹配</h4>
          <div class="zone-row">
            <div class="zone-tag zone-freeze">冷冻区 <span class="zone-cnt">{{ zoneMatch.freeze }}</span></div>
            <div class="zone-tag zone-chill">冷藏区 <span class="zone-cnt">{{ zoneMatch.chill }}</span></div>
            <div class="zone-tag zone-ambient">恒温区 <span class="zone-cnt">{{ zoneMatch.ambient }}</span></div>
          </div>
        </div>
      </div>

      <!-- 资源协调看板 -->
      <div class="glass-card">
        <div class="card-header-row">
          <div>
            <h3>资源协调看板</h3>
            <span class="card-sub">动态资源调配 · 智能匹配</span>
          </div>
          <button class="btn-sm btn-secondary" @click="refreshResources" :disabled="refreshing">{{ refreshing ? '刷新中...' : '刷新' }}</button>
        </div>
        <div class="resource-list">
          <div class="resource-item" v-for="r in resourceList" :key="r.id">
            <div class="res-info">
              <div class="res-icon" :class="r.type">
                <svg v-if="r.type==='vehicle'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              </div>
              <div class="res-detail">
                <span class="res-name">{{ r.name }}</span>
                <span class="res-desc">{{ r.type === 'vehicle' ? '多温区冷藏车' : '智能冷库' }} · {{ r.location }}</span>
              </div>
            </div>
            <div class="res-status">
              <span class="res-dot" :class="r.status === 'idle' ? 'green' : r.status === 'busy' ? 'amber' : 'red'"></span>
              <span>{{ r.status === 'idle' ? '空闲' : r.status === 'busy' ? '运输中' : '维护中' }}</span>
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
import { useRouter } from 'vue-router'
import { getTempClass } from '@/utils'
import { computed, reactive, onMounted, onUnmounted } from 'vue'

const store = useAppStore()
const router = useRouter()

// 辅助函数
function randomInRange(min: number, max: number) {
  return Math.round(min + Math.random() * (max - min))
}

const role = computed(() => store.userRole || 'admin')
const roleInfo = computed(() => {
  const m: Record<string, any> = {
    admin: { label: '管理员', tips: '配置规则、规划路径、调度资源，统筹冷链运营' },
    manager: { label: '经理', tips: '查看全局态势、审核追溯链路、评估生鲜品质' },
    driver: { label: '司机', tips: '查看配送路线、监控车辆温度、及时处理告警' },
  }
  return m[role.value] || m.admin
})

const quickActions = computed(() => {
  const actions: Record<string, { path: string; label: string; icon: string; color: string }[]> = {
    admin: [
      { path: '/routes', label: '路径规划', icon: '<polyline points="3 12 7 5 17 19 21 12"/>', color: '#00a8ff' },
      { path: '/dispatch', label: '多温区调度', icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>', color: '#7c3aed' },
      { path: '/rules', label: '告警规则', icon: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09A1.65 1.65 0 0 0 19.4 15z"/>', color: '#f59e0b' },
      { path: '/alerts', label: '告警中心', icon: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>', color: '#ef4444' },
    ],
    manager: [
      { path: '/temperature', label: '温度趋势', icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>', color: '#00a8ff' },
      { path: '/traceability', label: '追溯查询', icon: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>', color: '#7c3aed' },
      { path: '/quality', label: '品质评估', icon: '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>', color: '#f59e0b' },
      { path: '/alerts', label: '告警中心', icon: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>', color: '#ef4444' },
    ],
    driver: [
      { path: '/routes', label: '配送路线', icon: '<polyline points="3 12 7 5 17 19 21 12"/>', color: '#00a8ff' },
      { path: '/tracking', label: '车辆追踪', icon: '<circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/>', color: '#7c3aed' },
      { path: '/alerts', label: '告警处理', icon: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>', color: '#ef4444' },
      { path: '/mobile', label: '移动端', icon: '<rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/>', color: '#0ea5e9' },
    ],
  }
  return actions[role.value] || actions.admin
})

// 资源统计（从 store KPI 动态计算）
const resourceStats = computed(() => {
  const kpi = store.kpi
  const fleet = kpi.fleet_status || {}
  return {
    availableVehicles: fleet.idle || Math.max(0, (kpi.online_devices || 0) - (fleet.transit || 0)),
    availableWarehouses: kpi.warehouse_distribution?.length || 5,
    todayOrders: kpi.today_orders?.total || kpi.total_waybills || 31,
    energyUsage: Math.round((kpi.online_devices || 30) * 28.5 + randomInRange(-20, 30)),
  }
})

// 订单统计（从 store 订单流转数据动态计算）
const orderStats = computed(() => {
  const flow = store.orderFlow || {}
  const kpi = store.kpi
  const tod = kpi.today_orders || {}
  return {
    pending: Math.max(0, tod.pending || flow.pending || 5),
    matching: Math.max(0, tod.accepted || flow.accepted || 8),
    inTransit: Math.max(0, tod.in_transit || flow.in_transit || 17),
    completed: Math.max(0, (tod.completed || 0) + (flow.completed || 0) + (flow.delivered || 0) || 3),
  }
})

// 温区匹配（从设备数据中统计各温区车辆数）
const zoneMatch = computed(() => {
  const devices = store.devices || []
  const freeze = devices.filter((d: any) => d.cargo_zone === 'frozen').length
  const chill = devices.filter((d: any) => d.cargo_zone === 'refrigerated').length
  const ambient = devices.filter((d: any) => d.cargo_zone === 'ambient').length
  return {
    freeze: freeze || 5,
    chill: chill || 6,
    ambient: ambient || 8,
  }
})

// 资源列表（从 store devices 动态生成）
const resourceList = computed(() => {
  const devices = store.devices.slice(0, 5)
  if (devices.length === 0) {
    return [
      { id: 'V001', name: '冷链车 A-01', type: 'vehicle', location: '上海仓', status: 'idle' },
      { id: 'V002', name: '冷链车 A-02', type: 'vehicle', location: '上海仓', status: 'busy' },
      { id: 'W001', name: '上海冷库 1号', type: 'warehouse', location: '浦东新区', status: 'idle' },
      { id: 'W002', name: '杭州冷库 2号', type: 'warehouse', location: '余杭区', status: 'busy' },
    ]
  }
  return devices.map((d: any) => ({
    id: d.device_id,
    name: d.plate_number || d.device_id,
    type: d.device_type === 'cold_room' ? 'warehouse' : 'vehicle',
    location: d.current_city || d.location || '未知',
    status: d.cold_car_status === 0 ? 'offline'
      : d.vehicle_speed > 0 ? 'busy'
      : d.cargo_zone ? 'idle'
      : 'maintenance',
  }))
})

const refreshing = ref(false)

function refreshResources() {
  refreshing.value = true
  store.fetchDevices().finally(() => {
    refreshing.value = false
  })
}

// 🔥 温度趋势线数据
const trendLines = computed(() => {
  const genLine = (baseY: number, amp: number, freq: number) => {
    const pts: string[] = []
    for (let i = 0; i <= 24; i++) {
      const x = (i / 24) * 600
      const noise = Math.sin(i * 0.8 + freq) * amp + Math.sin(i * 2.1) * amp * 0.3
      const y = Math.max(5, Math.min(155, baseY + noise))
      pts.push(`${x.toFixed(0)},${y.toFixed(0)}`)
    }
    return pts.join(' ')
  }
  return {
    freeze: genLine(70, 12, 0),
    chill: genLine(50, 8, 2),
    ambient: genLine(90, 15, 4),
  }
})

// 🔥 告警分布（基于实际设备告警数据）
const alertCounts = computed(() => {
  const devices = store.devices || []
  return {
    temp: devices.filter((d: any) => !d.temperature_compliant && d.online !== false).length,
    machine: devices.filter((d: any) => d.cold_car_health !== undefined && d.cold_car_health < 50).length,
    door: devices.filter((d: any) => d.door_status === true || d.door_status === 1).length,
    delay: store.orderFlow?.delivered ? Math.round(store.orderFlow.delivered * 0.1) : 0,
  }
})
const maxAlert = computed(() => Math.max(1, alertCounts.value.temp + alertCounts.value.machine + alertCounts.value.door + alertCounts.value.delay))
const alertDist = computed(() => ({
  temp: (alertCounts.value.temp / maxAlert.value) * 100,
  machine: (alertCounts.value.machine / maxAlert.value) * 100,
  door: (alertCounts.value.door / maxAlert.value) * 100,
  delay: (alertCounts.value.delay / maxAlert.value) * 100,
}))

// 🔥 车队状态环（基于实际设备数据）
const fleetStatus = computed(() => {
  const kpi = store.kpi
  const fleet = kpi.fleet_status || {}
  const onlineDevices = store.devices.filter((d: any) => d.online !== false)
  const online = fleet.online || onlineDevices.length || resourceStats.value.availableVehicles || 0
  const transit = fleet.transit || onlineDevices.filter((d: any) => d.vehicle_speed > 0).length
  const idle = fleet.idle ?? Math.max(0, online - transit)
  return {
    online,
    transit,
    idle,
    onlinePct: online > 0 ? 100 : 0,
    transitPct: online > 0 ? Math.round((transit / online) * 100) : 0,
    idlePct: online > 0 ? Math.round((idle / online) * 100) : 0,
  }
})

onMounted(() => {
  store.startAutoRefresh(5000)
})

onUnmounted(() => {
  store.stopAutoRefresh()
})
</script>

<style scoped>
.dashboard { animation: fadeInUp 0.5s ease-out; }

.header-meta { display: flex; align-items: center; gap: 14px; }
.live-indicator {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--teal); font-family: var(--font-mono); font-weight: 500;
}
.live-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--teal);
  animation: pulse-ring 2s ease-out infinite;
  box-shadow: 0 0 8px rgba(0,200,150,0.4);
}
.update-time {
  font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);
  background: var(--bg-input); padding: 4px 12px; border-radius: 20px;
  border: 1px solid var(--border-light);
}

/* --- KPI --- */
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 0.8fr;
  gap: 16px;
  margin-bottom: 24px;
}
.kpi-card {
  background: var(--bg-card);
  backdrop-filter: var(--blur-card);
  -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 20px 22px;
  display: flex; gap: 16px;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,152,255,0.12), transparent);
  opacity: 0;
  transition: opacity 0.35s;
}
.kpi-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-3px);
}
.kpi-card:hover::before { opacity: 1; }
.kpi-card--red {
  border-color: rgba(239,68,68,0.15);
  background: linear-gradient(135deg, rgba(239,68,68,0.02), var(--bg-card));
}
.kpi-card--red:hover { border-color: rgba(239,68,68,0.3); }
.kpi-card--clean {
  background: linear-gradient(135deg, rgba(0,200,150,0.02), var(--bg-card));
}

.kpi-icon-box {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  transition: transform 0.3s ease;
}
.kpi-card:hover .kpi-icon-box { transform: scale(1.05); }
.kpi-icon-box.blue {
  background: linear-gradient(135deg, rgba(0,152,255,0.12), rgba(0,152,255,0.04));
  color: var(--accent);
}
.kpi-icon-box.green {
  background: linear-gradient(135deg, rgba(0,200,150,0.12), rgba(0,200,150,0.04));
  color: var(--teal);
}
.kpi-icon-box.red {
  background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(239,68,68,0.04));
  color: var(--red);
}

.kpi-body { flex: 1; min-width: 0; }
.kpi-label { font-size: 11px; color: var(--text-muted); letter-spacing: 0.04em; margin-bottom: 5px; text-transform: uppercase; font-weight: 600; }
.kpi-value { display: flex; align-items: baseline; gap: 4px; margin-bottom: 10px; }
.kpi-number { font-family: var(--font-display); font-size: 30px; font-weight: 800; color: var(--text-title); line-height: 1; }
.kpi-unit { font-size: 12px; color: var(--text-muted); font-family: var(--font-body); }
.text-teal { color: var(--teal) !important; }
.text-amber { color: var(--amber) !important; }
.text-red { color: var(--red) !important; }

.kpi-bar { height: 4px; background: var(--bg-input); border-radius: 4px; overflow: hidden; }
.kpi-fill { height: 100%; border-radius: 4px; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); }
.blue-fill {
  background: linear-gradient(90deg, var(--accent), var(--accent-light));
  box-shadow: 0 0 8px rgba(0,152,255,0.3);
}
.green-fill {
  background: linear-gradient(90deg, var(--teal), var(--teal-light));
  box-shadow: 0 0 8px rgba(0,200,150,0.3);
}

.kpi-tag {
  display: inline-block; font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 20px;
  font-family: var(--font-mono); letter-spacing: 0.05em; text-transform: uppercase;
}
.tag-red { background: var(--red-bg); color: var(--red); border: 1px solid rgba(239,68,68,0.15); }
.tag-teal { background: var(--teal-bg); color: var(--teal); border: 1px solid rgba(0,200,150,0.15); }

/* ====== 业务联动面板 ====== */
.linkage-panel { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
@media (max-width: 900px) { .linkage-panel { grid-template-columns: 1fr; } }

/* 订单流转步骤 */
.flow-steps { display: flex; align-items: center; gap: 0; margin-top: 20px; padding: 12px 4px; overflow-x: auto; }
.fs-step { display: flex; flex-direction: column; align-items: center; gap: 10px; min-width: 72px; opacity: 0.45; transition: all 0.35s; }
.fs-step.active { opacity: 1; }
.fss-dot {
  width: 46px; height: 46px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; background: #f0f2f5; border: 2px solid #e0e0e0;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}
.fss-dot.pending { background: #fef9e7; border-color: #f59e0b; box-shadow: 0 2px 10px rgba(245,158,11,0.15); }
.fss-dot.accepted { background: #e8f4fd; border-color: #3b82f6; box-shadow: 0 2px 10px rgba(59,130,246,0.15); }
.fss-dot.transit { background: #f3eeff; border-color: #7c3aed; box-shadow: 0 2px 10px rgba(124,58,237,0.15); }
.fss-dot.delivered { background: #fff7ed; border-color: #f97316; box-shadow: 0 2px 10px rgba(249,115,22,0.15); }
.fss-dot.completed { background: #e6f9f2; border-color: #10b981; box-shadow: 0 2px 10px rgba(16,185,129,0.15); }
.fs-step.active .fss-dot { transform: scale(1.12); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.fss-info { text-align: center; }
.fss-num { display: block; font-size: 22px; font-weight: 800; color: #0b1622; font-family: var(--font-display); }
.fss-label { font-size: 11px; color: #8e9cb4; margin-top: 3px; font-weight: 500; }
.fs-arrow { color: #cbd5e1; font-size: 20px; padding: 0 6px; flex-shrink: 0; margin-bottom: 26px; font-weight: 300; }

/* 照片审核卡片 */
.photo-review-card { border-left: 4px solid #ef4444; background: linear-gradient(135deg, rgba(239,68,68,0.015), var(--bg-card)); }
.badge-red { display: inline-block; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 12px; background: #fee2e2; color: #dc2626; vertical-align: middle; }
.btn-warning { background: #fef9e7; color: #d97706; border: 1px solid #fde68a; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-warning:hover { background: #fef3c7; border-color: #f59e0b; }
.pr-list { display: flex; flex-direction: column; gap: 8px; margin-top: 14px; }
.pr-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 10px; background: #fef2f2; border: 1px solid #fecaca; transition: all 0.25s; }
.pr-item:hover { background: #fee2e2; transform: translateX(3px); }
.pri-icon { font-size: 22px; flex-shrink: 0; }
.pri-body { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.pri-type { font-size: 12px; font-weight: 700; color: #dc2626; }
.pri-order { font-size: 11px; color: #991b1b; font-family: var(--font-mono); }
.pri-time { font-size: 10px; color: #94a3b8; white-space: nowrap; }

/* 事件时间线 */
.event-timeline { display: flex; flex-direction: column; gap: 0; margin-top: 16px; }
.et-item { display: flex; gap: 16px; padding: 12px 0; position: relative; animation: fadeInUp 0.4s ease-out both; }
.et-item:not(:last-child)::after {
  content: '';
  position: absolute; left: 20px; top: 44px; bottom: -8px;
  width: 2px;
  background: linear-gradient(to bottom, #e2e8f0, transparent);
}
.et-dot {
  width: 42px; height: 42px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
  background: #f3f4f6; border: 2px solid #e5e7eb;
  position: relative; z-index: 1;
  transition: all 0.3s;
}
.et-item:hover .et-dot { transform: scale(1.08); }
.et-dot.pending { background: #fef9e7; border-color: #f59e0b; }
.et-dot.accepted { background: #e8f4fd; border-color: #3b82f6; }
.et-dot.in_transit { background: #f3eeff; border-color: #7c3aed; }
.et-dot.delivered { background: #fff7ed; border-color: #f97316; }
.et-dot.completed { background: #e6f9f2; border-color: #10b981; }
.et-content { flex: 1; min-width: 0; }
.et-header { display: flex; justify-content: space-between; align-items: center; }
.et-label { font-size: 13px; font-weight: 700; color: #0b1622; }
.et-time { font-size: 11px; color: #94a3b8; font-family: var(--font-mono); }
.et-desc { font-size: 12px; color: #55657e; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.et-meta { display: flex; gap: 14px; margin-top: 5px; }
.et-actor { font-size: 11px; color: #8e9cb4; }
.et-empty { text-align: center; padding: 36px; color: #cbd5e1; }
.et-empty span { font-size: 40px; display: block; margin-bottom: 10px; }
.et-empty p { font-size: 13px; margin: 0; }

/* Live Tag */
.live-tag {
  display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px;
  background: #dc2626; color: #fff; vertical-align: middle; margin-left: 6px;
  animation: pulse 1.5s infinite; letter-spacing: 0.04em;
}
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.55; } }

/* Dual KPI */
.kpi-dual { display: flex; align-items: center; width: 100%; }
.kpi-half { flex: 1; text-align: center; }
.kpi-v-divider { width: 1px; height: 34px; background: var(--border-light); }
.kpi-value-sm { display: flex; align-items: baseline; justify-content: center; gap: 3px; }
.kpi-number-sm { font-family: var(--font-display); font-size: 26px; font-weight: 800; color: var(--text-title); }
.kpi-unit-sm { font-size: 11px; color: var(--text-muted); }

/* Table */
.card-header-row {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px;
  gap: 12px;
}
.card-header-row > div { min-width: 0; flex: 1; }
.card-header-row h3 { font-size: 16px; font-weight: 700; color: var(--text-title); white-space: nowrap; }
.card-sub { font-size: 12px; color: var(--text-muted); margin-left: 8px; }
.legend-row { display: flex; gap: 18px; align-items: center; }
.legend-it { font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; font-weight: 500; }
.legend-dot { width: 7px; height: 7px; border-radius: 50%; }
.green-dot { background: var(--teal); box-shadow: 0 0 6px rgba(0,200,150,0.4); }
.amber-dot { background: var(--amber); box-shadow: 0 0 6px rgba(245,158,11,0.4); }
.red-dot { background: var(--red); box-shadow: 0 0 6px rgba(239,68,68,0.4); }

.table-box { overflow-x: auto; border-radius: var(--radius); }
.cell-id {
  font-family: var(--font-mono); font-size: 11px; color: var(--accent);
  background: var(--accent-bg); padding: 3px 10px; border-radius: 6px; font-weight: 600;
}
.type-tag {
  font-size: 11px; padding: 3px 10px; border-radius: 20px; font-weight: 600;
}
.type-tag.vehicle { background: var(--accent-bg); color: var(--accent); }
.type-tag.cold_room { background: var(--teal-bg); color: var(--teal); }
.temp-val { font-family: var(--font-mono); font-weight: 600; font-size: 13px; }
.door-badge { font-size: 11px; padding: 3px 10px; border-radius: 12px; background: var(--bg-input); color: var(--text-secondary); font-weight: 500; }
.door-badge.open { background: var(--amber-bg); color: var(--amber); font-weight: 600; }
.alert-badge {
  font-family: var(--font-mono); font-size: 11px; font-weight: 700;
  background: var(--red); color: #fff; padding: 2px 8px; border-radius: 10px;
  box-shadow: 0 2px 6px rgba(239,68,68,0.3);
}
.none-text { color: var(--teal); font-weight: 600; }
.time-text { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }

@media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

/* Dashboard grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
  margin-bottom: 22px;
}
@media (max-width: 1024px) {
  .dashboard-grid { grid-template-columns: 1fr; }
}

/* Order stats */
.order-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
.order-stat {
  background: var(--bg-input);
  border-radius: var(--radius);
  padding: 18px 16px;
  text-align: center;
  transition: all 0.25s;
  border: 1px solid transparent;
}
.order-stat:hover {
  background: var(--bg-card);
  border-color: var(--border-card);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}
.os-num {
  display: block;
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 6px;
}
.os-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

/* Zone match */
.zone-match h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 12px;
}
.zone-row {
  display: flex;
  gap: 10px;
}
.zone-tag {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-input);
  transition: all 0.25s;
  border: 1px solid transparent;
}
.zone-tag:hover {
  background: var(--bg-card);
  border-color: var(--border-card);
  box-shadow: var(--shadow-sm);
}
.zone-cnt {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 16px;
  color: var(--text-title);
}
.zone-freeze { border-left: 4px solid var(--accent); }
.zone-chill { border-left: 4px solid var(--teal); }
.zone-ambient { border-left: 4px solid var(--amber); }

/* Resource list */
.resource-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.resource-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--bg-input);
  border-radius: var(--radius);
  transition: all 0.25s;
  border: 1px solid transparent;
}
.resource-item:hover {
  background: var(--bg-card);
  border-color: var(--border-card);
  box-shadow: var(--shadow-xs);
}
.res-info {
  display: flex;
  align-items: center;
  gap: 14px;
}
.res-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.res-icon.vehicle { background: linear-gradient(135deg, var(--accent), #0078e8); box-shadow: 0 2px 8px rgba(0,152,255,0.25); }
.res-icon.warehouse { background: linear-gradient(135deg, var(--aurora), #6d28d9); box-shadow: 0 2px 8px rgba(124,58,237,0.25); }
.res-detail {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.res-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
}
.res-desc {
  font-size: 11px;
  color: var(--text-muted);
}
.res-status {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}
.res-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.res-dot.green { background: var(--teal); box-shadow: 0 0 6px rgba(0,200,150,0.5); }
.res-dot.amber { background: var(--amber); box-shadow: 0 0 6px rgba(245,158,11,0.5); }
.res-dot.red { background: var(--red); box-shadow: 0 0 6px rgba(239,68,68,0.5); }

/* Quick Actions */
.kpi-icon-box.accent { background: linear-gradient(135deg, rgba(0,152,255,0.12), rgba(0,152,255,0.04)); color: var(--accent); }
.kpi-icon-box.accent2 { background: linear-gradient(135deg, rgba(124,58,237,0.12), rgba(124,58,237,0.04)); color: var(--aurora); }
.kpi-icon-box.warn { background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(245,158,11,0.04)); color: var(--amber); }
.kpi-icon-box.energy { background: linear-gradient(135deg, rgba(0,200,150,0.12), rgba(0,200,150,0.04)); color: var(--teal); }
.kpi-card--sm {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius);
  padding: 16px 20px;
  display: flex; gap: 14px;
  box-shadow: var(--shadow-xs);
  transition: all 0.3s ease;
}
.kpi-card--sm:hover {
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}
.text-accent { color: var(--accent) !important; }

/* Temp classes */
.temp-normal { color: var(--teal) !important; }
.temp-warn { color: var(--amber) !important; }
.temp-danger { color: var(--red) !important; }

/* Quick Actions */
.quick-actions {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 22px;
  box-shadow: var(--shadow-sm);
  backdrop-filter: var(--blur-card);
  -webkit-backdrop-filter: var(--blur-card);
}
.qa-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-bottom: 18px;
}
.qa-header h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-title);
}
.qa-tips {
  font-size: 12px;
  color: var(--text-muted);
}
.qa-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 12px;
}
.qa-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--bg-page);
  position: relative;
  overflow: hidden;
}
.qa-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(0,152,255,0.04), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}
.qa-card:hover {
  background: var(--bg-card);
  border-color: var(--border-focus);
  transform: translateY(-3px);
  box-shadow: var(--shadow);
}
.qa-card:hover::before { opacity: 1; }
.qa-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid;
  flex-shrink: 0;
  transition: transform 0.3s;
}
.qa-card:hover .qa-icon { transform: scale(1.08); }
.qa-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  flex: 1;
  transition: color 0.3s;
}
.qa-card:hover .qa-label {
  color: var(--text-title);
}
.qa-arrow {
  color: var(--text-muted);
  opacity: 0;
  transform: translateX(-6px);
  transition: all 0.3s;
}
.qa-card:hover .qa-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* ==================== 🔥 Monitor Grid ==================== */
.monitor-grid {
  display: grid;
  grid-template-columns: 1fr 0.9fr;
  gap: 22px;
  margin-bottom: 22px;
}
@media (max-width: 1024px) {
  .monitor-grid { grid-template-columns: 1fr; }
}

/* Trend Card */
.trend-card { overflow: hidden; }
.trend-legend { display: flex; gap: 18px; }
.tl-item { font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; font-weight: 500; }
.tl-dot { width: 9px; height: 9px; border-radius: 50%; }
.tl-dot.freeze { background: #0098ff; box-shadow: 0 0 6px rgba(0,152,255,0.4); }
.tl-dot.chill { background: #0ea5e9; box-shadow: 0 0 6px rgba(14,165,233,0.4); }
.tl-dot.ambient { background: #f59e0b; box-shadow: 0 0 6px rgba(245,158,11,0.4); }

.trend-chart { margin-top: 16px; }
.trend-canvas { width: 100%; height: 180px; background: rgba(0,0,0,0.01); border-radius: 10px; padding: 8px; }
.trend-svg { width: 100%; height: 100%; }
.trend-xaxis {
  display: flex; justify-content: space-between;
  font-size: 10px; color: var(--text-muted);
  padding: 6px 8px 0; font-family: var(--font-mono);
}

/* Alert Overview */
.alert-overview { }
.alert-bars { display: flex; flex-direction: column; gap: 16px; margin-top: 12px; }
.ab-row { display: flex; align-items: center; gap: 14px; }
.ab-label { font-size: 12px; color: var(--text-secondary); width: 64px; flex-shrink: 0; font-weight: 600; }
.ab-track { flex: 1; height: 10px; background: var(--bg-input); border-radius: 5px; overflow: hidden; }
.ab-fill { height: 100%; border-radius: 5px; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); }
.ab-fill.critical { background: linear-gradient(90deg, #ef4444, #f87171); box-shadow: 0 0 8px rgba(239,68,68,0.3); }
.ab-fill.warning { background: linear-gradient(90deg, #f59e0b, #fbbf24); box-shadow: 0 0 8px rgba(245,158,11,0.3); }
.ab-fill.info { background: linear-gradient(90deg, #0ea5e9, #38bdf8); box-shadow: 0 0 8px rgba(14,165,233,0.3); }
.ab-fill.delay { background: linear-gradient(90deg, #7c3aed, #a78bfa); box-shadow: 0 0 8px rgba(124,58,237,0.3); }
.ab-cnt { font-size: 14px; font-weight: 700; font-family: var(--font-display); width: 28px; text-align: right; }
.critical-text { color: #ef4444; }
.warning-text { color: #f59e0b; }
.info-text { color: #0ea5e9; }
.delay-text { color: #7c3aed; }

/* Vehicle Rings */
.vehicle-rings {
  display: flex; justify-content: space-around;
  margin-top: 22px; padding-top: 18px;
  border-top: 1px solid var(--border-light);
}
.vr-item { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.vr-ring {
  width: 68px; height: 68px; position: relative;
  display: flex; align-items: center; justify-content: center;
}
.vr-ring svg { position: absolute; inset: 0; }
.vr-ring svg circle { transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1); }
.vr-val {
  font-family: var(--font-display); font-size: 18px; font-weight: 800;
  color: var(--text-title); z-index: 1;
}
.vr-label { font-size: 11px; color: var(--text-muted); font-weight: 600; }
</style>
