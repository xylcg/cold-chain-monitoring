<template>
  <div class="warehouse-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">仓管维修工作台</h2>
        <span class="page-subtitle">品质AI质检 · 拍照审核 · 冷机故障预测 · 仓储管理</span>
      </div>
      <div class="header-right">
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span>实时监控中 · 更新间隔 10s</span>
        </div>
        <div class="date-display">{{ currentDate }}</div>
      </div>
    </div>

    <!-- ============ Tab 切换：概览 / 订单审核 / 库存管理 / 品质质检 / 拍照审核 / 故障预测 ============ -->
    <div class="main-tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">🏠 工作概览</button>
      <button class="tab-btn" :class="{ active: activeTab === 'order-review' }" @click="activeTab = 'order-review'; loadOrderReview()">📋 订单审核</button>
      <button class="tab-btn" :class="{ active: activeTab === 'inventory' }" @click="activeTab = 'inventory'">📦 库存管理</button>
      <button class="tab-btn" :class="{ active: activeTab === 'quality' }" @click="activeTab = 'quality'">🤖 品质质检</button>
      <button class="tab-btn" :class="{ active: activeTab === 'review' }" @click="activeTab = 'review'">📷 拍照审核</button>
      <button class="tab-btn" :class="{ active: activeTab === 'maintenance' }" @click="activeTab = 'maintenance'">🔧 故障预测</button>
    </div>

    <!-- ============ Tab 0：工作概览（新增） ============ -->
    <div v-show="activeTab === 'overview'" class="tab-panel">
      <!-- 关键指标 4 列 -->
      <div class="overview-kpi">
        <div class="ov-kpi-card blue-glow">
          <div class="ovk-icon">📦</div>
          <div class="ovk-body">
            <div class="ovk-value">{{ invSummary?.data?.total_kg || 0 }}<small>kg</small></div>
            <div class="ovk-label">仓库总库存</div>
          </div>
          <div class="ovk-spark">
            <svg viewBox="0 0 80 24" class="spark-svg"><polyline :points="sparkData.inventory" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </div>
        </div>
        <div class="ov-kpi-card amber-glow">
          <div class="ovk-icon">⏰</div>
          <div class="ovk-body">
            <div class="ovk-value">{{ invSummary?.data?.total_near_expiry || 0 }}<small>批</small></div>
            <div class="ovk-label">临期预警</div>
          </div>
          <div class="ovk-spark warn">
            <svg viewBox="0 0 80 24" class="spark-svg"><polyline :points="sparkData.expiry" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </div>
        </div>
        <div class="ov-kpi-card green-glow">
          <div class="ovk-icon">✅</div>
          <div class="ovk-body">
            <div class="ovk-value">{{ reviewStats?.approved || 0 }}<small>单</small></div>
            <div class="ovk-label">今日审核通过</div>
          </div>
          <div class="ovk-spark success">
            <svg viewBox="0 0 80 24" class="spark-svg"><polyline :points="sparkData.review" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </div>
        </div>
        <div class="ov-kpi-card purple-glow">
          <div class="ovk-icon">🔧</div>
          <div class="ovk-body">
            <div class="ovk-value">{{ maintStats?.high_risk || 0 }}<small>台</small></div>
            <div class="ovk-label">高风险设备</div>
          </div>
          <div class="ovk-spark danger">
            <svg viewBox="0 0 80 24" class="spark-svg"><polyline :points="sparkData.maint" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </div>
        </div>
      </div>

      <!-- 库存水位 + 待办任务 双栏 -->
      <div class="ov-grid">
        <!-- 库存水位 -->
        <div class="glass-card">
          <div class="card-header-row">
            <h3>📊 各仓库库存水位</h3>
            <span class="card-sub">{{ invSummary?.data?.total_warehouses || 0 }} 座冷库</span>
          </div>
          <div class="water-levels" v-if="invSummary?.data?.details">
            <div v-for="wh in invSummary.data.details.slice(0, 4)" :key="wh.warehouse_id" class="wl-item">
              <div class="wl-header">
                <span class="wl-name">{{ wh.warehouse_name }}</span>
                <span class="wl-pct">{{ Math.round((wh.frozen_kg + wh.refrigerated_kg + wh.ambient_kg) / (invSummary.data.total_kg || 1) * 100) }}%</span>
              </div>
              <div class="wl-bar-stacked">
                <div class="wl-seg frozen" :style="{ flex: wh.frozen_kg }" title="冷冻"></div>
                <div class="wl-seg chilled" :style="{ flex: wh.refrigerated_kg }" title="冷藏"></div>
                <div class="wl-seg ambient" :style="{ flex: wh.ambient_kg }" title="恒温"></div>
              </div>
              <div class="wl-footer">
                <span>{{ wh.location }}</span>
                <span v-if="wh.near_expiry_count" class="wl-warn">⚠ {{ wh.near_expiry_count }}批临期</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 待办任务 -->
        <div class="glass-card">
          <div class="card-header-row">
            <h3>📋 今日待办</h3>
            <span class="card-sub">优先级排序</span>
          </div>
          <div class="todo-list">
            <div class="todo-item urgent" v-if="maintStats?.high_risk > 0">
              <span class="todo-icon">🔴</span>
              <div class="todo-body">
                <span class="todo-title">冷机故障风险</span>
                <span class="todo-desc">{{ maintStats?.high_risk || 0 }} 台设备需要立即检修</span>
              </div>
              <button class="btn btn-sm btn-danger" @click="activeTab = 'maintenance'">处理</button>
            </div>
            <div class="todo-item important" v-if="reviewStats?.pending > 0">
              <span class="todo-icon">🟡</span>
              <div class="todo-body">
                <span class="todo-title">拍照待审核</span>
                <span class="todo-desc">{{ reviewStats?.pending || 0 }} 张照片等待仓管审核</span>
              </div>
              <button class="btn btn-sm btn-warn" @click="activeTab = 'review'">审核</button>
            </div>
            <div class="todo-item" v-if="orderReviewStats?.pending > 0">
              <span class="todo-icon">📋</span>
              <div class="todo-body">
                <span class="todo-title">订单待审核</span>
                <span class="todo-desc">{{ orderReviewStats?.pending || 0 }} 个订单等待仓库确认</span>
              </div>
              <button class="btn btn-sm btn-primary" @click="activeTab = 'order-review'; loadOrderReview()">处理</button>
            </div>
            <div class="todo-item done" v-if="invSummary?.data?.total_expired > 0">
              <span class="todo-icon">⚠️</span>
              <div class="todo-body">
                <span class="todo-title">过期库存清理</span>
                <span class="todo-desc">{{ invSummary?.data?.total_expired || 0 }} 批货物已过期需处理</span>
              </div>
              <button class="btn btn-sm" @click="activeTab = 'inventory'">查看</button>
            </div>
            <div class="todo-empty" v-if="!hasTodos">✅ 今日暂无紧急待办事项</div>
          </div>
        </div>
      </div>

      <!-- 最近操作日志 -->
      <div class="glass-card">
        <div class="card-header-row">
          <h3>🕐 最近操作记录</h3>
          <button class="btn btn-sm" @click="refreshAll">🔄 刷新全部</button>
        </div>
        <div class="log-stream">
          <div class="log-item" v-for="(log, i) in recentLogs" :key="i">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-tag" :class="log.type">{{ log.tag }}</span>
            <span class="log-msg">{{ log.msg }}</span>
          </div>
          <div class="log-empty" v-if="recentLogs.length === 0">暂无操作记录</div>
        </div>
      </div>

      <!-- ====== 订单流转同步面板（与司机/客户联动） ====== -->
      <div class="glass-card">
        <div class="card-header-row">
          <div>
            <h3>📦 订单流转同步 <span class="live-tag">LIVE</span></h3>
            <span class="card-sub">客户下单 → 司机接单 → 配送 → 签收 · 实时追踪</span>
          </div>
          <span class="card-sub">共 {{ store.orderFlow.total }} 单</span>
        </div>
        <div class="order-sync-steps">
          <div class="oss-step" :class="{ active: store.orderFlow.pending > 0 }">
            <span class="oss-icon">📝</span>
            <span class="oss-num">{{ store.orderFlow.pending }}</span>
            <span class="oss-label">待接单</span>
          </div>
          <span class="oss-arrow">→</span>
          <div class="oss-step" :class="{ active: store.orderFlow.accepted > 0 }">
            <span class="oss-icon">📸</span>
            <span class="oss-num">{{ store.orderFlow.accepted }}</span>
            <span class="oss-label">已接单</span>
          </div>
          <span class="oss-arrow">→</span>
          <div class="oss-step" :class="{ active: store.orderFlow.in_transit > 0 }">
            <span class="oss-icon">🚀</span>
            <span class="oss-num">{{ store.orderFlow.in_transit }}</span>
            <span class="oss-label">配送中</span>
          </div>
          <span class="oss-arrow">→</span>
          <div class="oss-step" :class="{ active: store.orderFlow.delivered > 0 }">
            <span class="oss-icon">📦</span>
            <span class="oss-num">{{ store.orderFlow.delivered }}</span>
            <span class="oss-label">已送达</span>
          </div>
          <span class="oss-arrow">→</span>
          <div class="oss-step" :class="{ active: store.orderFlow.completed > 0 }">
            <span class="oss-icon">✅</span>
            <span class="oss-num">{{ store.orderFlow.completed }}</span>
            <span class="oss-label">已签收</span>
          </div>
        </div>
        <!-- 最近订单快照 -->
        <div class="oss-recent" v-if="store.orderFlow.all_orders.length > 0">
          <div class="oss-recent-item" v-for="o in store.orderFlow.all_orders.slice(0, 3)" :key="o.order_id">
            <span class="ossr-status" :class="o.status">{{ statusLabel(o.status) }}</span>
            <span class="ossr-id">{{ o.order_id }}</span>
            <span class="ossr-cargo">{{ o.cargo_name }}</span>
            <span class="ossr-route">{{ o.origin }} → {{ o.destination }}</span>
            <span class="ossr-driver" v-if="o.driver_name">{{ o.driver_name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ Tab 1：订单审核 ============ -->
    <div v-show="activeTab === 'order-review'" class="tab-panel">
      <div class="section-header">
        <h3>📋 订单审核</h3>
        <span class="card-badge badge-purple">顾客订单 · 仓库审核</span>
        <div class="review-stats-inline" v-if="orderReviewStats">
          <span class="rsi-item rsi-pending">待审 {{ orderReviewStats.pending || 0 }}</span>
          <span class="rsi-item rsi-approved">已通过 {{ orderReviewStats.approved || 0 }}</span>
          <span class="rsi-item rsi-rejected">已驳回 {{ orderReviewStats.rejected || 0 }}</span>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <button class="btn btn-sm" :class="{ active: orderReviewFilter === 'pending' }" @click="orderReviewFilter = 'pending'; loadOrderReview()">待审核</button>
          <button class="btn btn-sm" :class="{ active: orderReviewFilter === 'approved' }" @click="orderReviewFilter = 'approved'; loadOrderReview()">已通过</button>
          <button class="btn btn-sm" :class="{ active: orderReviewFilter === 'rejected' }" @click="orderReviewFilter = 'rejected'; loadOrderReview()">已驳回</button>
          <button class="btn btn-sm" :class="{ active: orderReviewFilter === 'all' }" @click="orderReviewFilter = 'all'; loadOrderReview()">全部</button>
        </div>
        <button class="btn btn-primary btn-sm" @click="loadOrderReview" :disabled="orderReviewLoading">
          {{ orderReviewLoading ? '加载中...' : '刷新列表' }}
        </button>
      </div>

      <!-- 审核订单列表 -->
      <div class="glass-card" v-if="orderReviewList.length > 0">
        <div class="order-review-list">
          <div
            v-for="order in orderReviewList"
            :key="order.order_id"
            class="or-item"
            :class="'or-' + (order.review_status || 'pending')"
          >
            <div class="or-header">
              <div class="or-left">
                <span class="or-id">{{ order.order_id }}</span>
                <span class="or-status-tag" :class="order.status">{{ statusMap[order.status] || order.status }}</span>
                <span v-if="order.review_status === 'approved'" class="or-review-tag approved">✅ 已通过</span>
                <span v-else-if="order.review_status === 'rejected'" class="or-review-tag rejected">❌ 已驳回</span>
                <span v-else class="or-review-tag pending">⏳ 待审核</span>
              </div>
              <span class="or-price">¥{{ order.price?.toLocaleString() }}</span>
            </div>
            <div class="or-body">
              <div class="or-info-row">
                <span class="or-label">货物</span>
                <span>{{ order.cargo_name }} · {{ order.cargo_category }}</span>
              </div>
              <div class="or-info-row">
                <span class="or-label">路线</span>
                <span>{{ order.origin }} → {{ order.destination }}</span>
              </div>
              <div class="or-info-row">
                <span class="or-label">数量</span>
                <span>{{ order.quantity }}{{ order.unit }}</span>
              </div>
              <div class="or-info-row">
                <span class="or-label">温区</span>
                <span class="zone-badge" :class="getZoneClass(order.zone_name)">{{ order.zone_name }}</span>
                <span class="or-temp">{{ order.temperature_requirement }}</span>
              </div>
              <div class="or-info-row">
                <span class="or-label">司机</span>
                <span class="text-accent">{{ order.driver_name || '—' }}</span>
              </div>
              <div class="or-info-row">
                <span class="or-label">收件人</span>
                <span>{{ order.receiver || '—' }} {{ order.receiver_phone }}</span>
              </div>
              <div class="or-info-row">
                <span class="or-label">时间</span>
                <span>{{ formatOrderTime(order.created_at) }}</span>
              </div>
              <div class="or-info-row" v-if="order.review_notes">
                <span class="or-label">意见</span>
                <span :class="order.review_status === 'rejected' ? 'text-red' : 'text-teal'">{{ order.review_notes }}</span>
              </div>
            </div>
            <!-- 待审核才显示操作按钮 -->
            <div class="or-actions" v-if="!order.review_status || order.review_status === 'pending'">
              <button class="btn btn-approve" @click="approveOrder(order)">✅ 审核通过</button>
              <button class="btn btn-reject" @click="openOrderRejectDialog(order)">❌ 驳回</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="glass-card" v-else>
        <div class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--border)" stroke-width="1.5">
            <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>
            <rect x="9" y="3" width="6" height="4" rx="1"/>
          </svg>
          <p>暂无{{ orderReviewFilterText }}的订单</p>
          <span>顾客下单后，司机接单的订单将在此处显示</span>
        </div>
      </div>

      <!-- 订单驳回弹窗 -->
      <div class="photo-modal-overlay" v-if="orderRejectDialog.target" @click="orderRejectDialog.target = null">
        <div class="reject-dialog" @click.stop>
          <h4>驳回订单 — {{ orderRejectDialog.target.order_id }}</h4>
          <p class="reject-tip">驳回后订单将回到待接单状态，其他司机可重新接单</p>
          <textarea v-model="orderRejectDialog.notes" placeholder="请填写驳回原因..." rows="3" class="reject-textarea"></textarea>
          <div class="photo-actions">
            <button class="btn btn-cancel" @click="orderRejectDialog.target = null">取消</button>
            <button class="btn btn-reject" :disabled="!orderRejectDialog.notes.trim()" @click="confirmOrderReject">确认驳回</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ Tab 0：库存管理 ============ -->
    <div v-show="activeTab === 'inventory'" class="tab-panel">
      <!-- 库存总览统计 -->
      <div class="stats-row" v-if="invSummary">
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(0,168,255,0.12);color:var(--accent)">📦</div>
          <div class="stat-info">
            <div class="stat-value">{{ invSummary.data?.total_kg || 0 }}<small style="font-size:14px">kg</small></div>
            <div class="stat-label">总库存量</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:var(--amber-bg);color:var(--amber)">⏰</div>
          <div class="stat-info">
            <div class="stat-value text-amber">{{ invSummary.data?.total_near_expiry || 0 }}</div>
            <div class="stat-label">临期批次</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:var(--red-bg);color:var(--red)">❌</div>
          <div class="stat-info">
            <div class="stat-value text-red">{{ invSummary.data?.total_expired || 0 }}</div>
            <div class="stat-label">已过期</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(0,210,160,0.12);color:var(--teal)">🏭</div>
          <div class="stat-info">
            <div class="stat-value">{{ invSummary.data?.total_warehouses || 0 }}</div>
            <div class="stat-label">覆盖冷库</div>
          </div>
        </div>
      </div>

      <!-- 各仓库库存汇总 -->
      <div class="glass-card" v-if="invSummary">
        <div class="card-header">
          <span>各仓库库存分布</span>
          <button class="btn btn-sm" @click="refreshInventory" :disabled="invLoading">{{ invLoading ? '加载中...' : '刷新' }}</button>
        </div>
        <div class="wh-summary-grid">
          <div v-for="wh in invSummary.data?.details" :key="wh.warehouse_id" class="wh-summary-card">
            <div class="wh-summary-name">{{ wh.warehouse_name }}</div>
            <div class="wh-summary-loc">{{ wh.location }}</div>
            <div class="wh-summary-bars">
              <div class="wh-bar-row">
                <span class="wh-bar-label">冷冻</span>
                <div class="wh-bar-bg"><div class="wh-bar-fill frozen-fill" :style="{ width: Math.min(wh.frozen_kg / (invSummary.data?.total_kg || 1) * 500, 100) + '%' }"></div></div>
                <span class="wh-bar-val">{{ wh.frozen_kg }}kg</span>
              </div>
              <div class="wh-bar-row">
                <span class="wh-bar-label">冷藏</span>
                <div class="wh-bar-bg"><div class="wh-bar-fill refrig-fill" :style="{ width: Math.min(wh.refrigerated_kg / (invSummary.data?.total_kg || 1) * 500, 100) + '%' }"></div></div>
                <span class="wh-bar-val">{{ wh.refrigerated_kg }}kg</span>
              </div>
              <div class="wh-bar-row">
                <span class="wh-bar-label">恒温</span>
                <div class="wh-bar-bg"><div class="wh-bar-fill amb-fill" :style="{ width: Math.min(wh.ambient_kg / (invSummary.data?.total_kg || 1) * 500, 100) + '%' }"></div></div>
                <span class="wh-bar-val">{{ wh.ambient_kg }}kg</span>
              </div>
            </div>
            <div class="wh-summary-alerts">
              <span v-if="wh.near_expiry_count" class="wh-tag tag-near">⏰ 临期{{ wh.near_expiry_count }}批</span>
              <span v-if="wh.expired_count" class="wh-tag tag-expired">❌ 过期{{ wh.expired_count }}批</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 入库/出库操作 -->
      <div class="two-col">
        <!-- 入库表单 -->
        <div class="glass-card">
          <div class="card-header"><span>📥 入库操作</span></div>
          <div class="op-form">
            <div class="form-row">
              <label>目标冷库</label>
              <select v-model="inboundForm.warehouse_id" class="form-select">
                <option value="">请选择冷库</option>
                <option v-for="w in warehouseList" :key="w.warehouse_id" :value="w.warehouse_id">{{ w.warehouse_name }}</option>
              </select>
            </div>
            <div class="form-row">
              <label>温区</label>
              <select v-model="inboundForm.zone" class="form-select">
                <option value="">请选择温区</option>
                <option value="frozen">冷冻区 (-20℃)</option>
                <option value="refrigerated">冷藏区 (0~4℃)</option>
                <option value="ambient">恒温区 (18~24℃)</option>
              </select>
            </div>
            <div class="form-row">
              <label>产品名称</label>
              <input v-model="inboundForm.product_name" class="form-input" placeholder="如：冷冻牛肉" />
            </div>
            <div class="form-row">
              <label>品类</label>
              <input v-model="inboundForm.category" class="form-input" placeholder="如：肉类/海鲜/乳制品" />
            </div>
            <div class="form-row split">
              <div class="form-half">
                <label>数量(kg)</label>
                <input v-model.number="inboundForm.quantity_kg" type="number" class="form-input" placeholder="0" />
              </div>
              <div class="form-half">
                <label>保鲜期(天)</label>
                <input v-model.number="inboundForm.shelf_life_days" type="number" class="form-input" placeholder="30" />
              </div>
            </div>
            <div class="form-row">
              <label>目标温度(℃)</label>
              <input v-model.number="inboundForm.target_temp_c" type="number" class="form-input" placeholder="-18" />
            </div>
            <div class="form-row">
              <label>备注</label>
              <input v-model="inboundForm.notes" class="form-input" placeholder="入库备注（选填）" />
            </div>
            <button class="btn btn-primary" style="width:100%;margin-top:8px" @click="doInbound" :disabled="inboundLoading">
              {{ inboundLoading ? '入库中...' : '确认入库' }}
            </button>
          </div>
        </div>

        <!-- 出库表单 -->
        <div class="glass-card">
          <div class="card-header"><span>📤 出库操作</span></div>
          <div class="op-form">
            <div class="form-row">
              <label>选择库存记录</label>
              <select v-model="outboundForm.inventory_id" class="form-select" @change="onOutboundSelect">
                <option value="">请选择</option>
                <option v-for="inv in inventoryList" :key="inv.id" :value="inv.id">
                  [{{ inv.warehouse_name }}] {{ inv.product_name }} - {{ inv.quantity_kg }}kg {{ inv.status === 'near_expiry' ? '(临期)' : inv.status === 'expired' ? '(过期)' : '' }}
                </option>
              </select>
            </div>
            <div class="form-row" v-if="selectedInv">
              <div class="inv-detail">
                <div class="inv-detail-row"><span>仓库</span><strong>{{ selectedInv.warehouse_name }}</strong></div>
                <div class="inv-detail-row"><span>产品</span><strong>{{ selectedInv.product_name }}</strong></div>
                <div class="inv-detail-row"><span>温区</span><strong>{{ selectedInv.zone_label }}</strong></div>
                <div class="inv-detail-row"><span>当前库存</span><strong class="text-amber">{{ selectedInv.quantity_kg }}kg</strong></div>
                <div class="inv-detail-row"><span>到期日</span><strong :class="selectedInv.status === 'near_expiry' ? 'text-red' : ''">{{ selectedInv.expiry_date }}</strong></div>
              </div>
            </div>
            <div class="form-row">
              <label>出库数量(kg)</label>
              <input v-model.number="outboundForm.quantity_kg" type="number" class="form-input" placeholder="0" />
            </div>
            <div class="form-row">
              <label>备注</label>
              <input v-model="outboundForm.notes" class="form-input" placeholder="出库备注（选填）" />
            </div>
            <button class="btn btn-primary" style="width:100%;margin-top:8px;background:linear-gradient(135deg,var(--amber),#f59e0b)" @click="doOutbound" :disabled="outboundLoading">
              {{ outboundLoading ? '出库中...' : '确认出库' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 库存列表 -->
      <div class="glass-card">
        <div class="card-header">
          <span>库存明细列表</span>
          <div class="toolbar-right">
            <select v-model="invFilter.warehouse_id" class="form-select form-select-sm" @change="loadInventory">
              <option value="">全部冷库</option>
              <option v-for="w in warehouseList" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
            <select v-model="invFilter.zone" class="form-select form-select-sm" @change="loadInventory">
              <option value="">全部温区</option>
              <option value="frozen">冷冻区</option>
              <option value="refrigerated">冷藏区</option>
              <option value="ambient">恒温区</option>
            </select>
            <select v-model="invFilter.status" class="form-select form-select-sm" @change="loadInventory">
              <option value="">全部状态</option>
              <option value="normal">正常</option>
              <option value="near_expiry">临期</option>
              <option value="expired">过期</option>
            </select>
            <input v-model="invFilter.keyword" class="form-input form-input-sm" placeholder="搜索产品..." @keyup.enter="loadInventory" />
          </div>
        </div>
        <div class="inv-table-wrap" v-if="inventoryList.length > 0">
          <table class="inv-table">
            <thead>
              <tr>
                <th>编号</th><th>仓库</th><th>产品</th><th>品类</th><th>温区</th><th>数量(kg)</th><th>目标温度</th><th>到期日</th><th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="inv in inventoryList" :key="inv.id" :class="'row-' + inv.status">
                <td class="mono">{{ inv.id }}</td>
                <td>{{ inv.warehouse_name }}</td>
                <td>{{ inv.product_name }}</td>
                <td>{{ inv.category }}</td>
                <td>{{ inv.zone_label }}</td>
                <td class="num">{{ inv.quantity_kg }}</td>
                <td class="num">{{ inv.target_temp_c }}℃</td>
                <td :class="inv.status === 'near_expiry' ? 'text-red' : inv.status === 'expired' ? 'text-red' : ''">{{ inv.expiry_date }}</td>
                <td><span class="inv-status" :class="'status-' + inv.status">{{ inv.status === 'normal' ? '正常' : inv.status === 'near_expiry' ? '临期' : '过期' }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">暂无库存数据</div>
      </div>
    </div>


    <!-- ============ 第一部分：品质AI质检（功能7） ============ -->
    <div class="section-block" v-show="activeTab === 'quality'">
      <div class="section-header">
        <h3>生鲜品质AI评估</h3>
        <span class="card-badge badge-green">功能7 · AI品质质检</span>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card" v-for="s in qualityStatsCards" :key="s.label">
          <div class="stat-icon" :style="{background:s.bg,color:s.color}">{{ s.icon }}</div>
          <div class="stat-info">
            <div class="stat-value" :style="{color:s.color}">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <!-- AI识别上传区 -->
      <div class="glass-card">
        <div class="card-header">
          <span>🤖 AI图片识别</span>
          <span class="header-tip">上传生鲜图片，AI自动识别品类与品质</span>
        </div>

        <div class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
          <input type="file" ref="uploadInput" accept="image/jpeg,image/png,image/jpg,image/webp" class="hidden-input" @change="handleFileSelect" />
          <div v-if="uploadedImage" class="upload-preview">
            <img :src="uploadedImage" class="preview-img" />
            <div class="preview-overlay">
              <div v-if="assessing" class="assessing-loader">
                <div class="loader-ring"></div>
                <span>AI正在分析中...</span>
              </div>
              <span v-else class="preview-status">✓ 已上传，点击重新选择</span>
            </div>
            <span class="preview-close" @click.stop="clearUpload">✕</span>
          </div>
          <div v-else class="upload-placeholder">
            <div class="upload-icon-wrap">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.35">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <h3>点击或拖拽图片到此处</h3>
            <p>支持 JPG、PNG、WEBP 格式，最大10MB</p>
          </div>
        </div>

        <!-- 评估结果 -->
        <div v-if="assessResult" class="result-section">
          <div class="grade-badge" :style="{background:getGradeColor(assessResult.grade)}">
            <span class="grade-text">{{ assessResult.grade }}</span>
            <span class="grade-score">{{ assessResult.quality_score }}分</span>
          </div>
          <div class="result-grid">
            <div class="result-card">
              <div class="rc-title">🤖 AI视觉评估</div>
              <div class="rc-content">
                <div class="info-row"><span>识别品类</span><strong>{{ assessResult.product_type || '未知' }}</strong></div>
                <div class="info-row"><span>品质评分</span><strong>{{ assessResult.quality_score || 0 }}分</strong></div>
                <div class="info-row"><span>置信度</span><strong>{{ ((assessResult.confidence || 0) * 100).toFixed(1) }}%</strong></div>
                <div class="info-row"><span>储存天数</span><strong>{{ assessResult.storage_days }}天</strong></div>
                <div class="info-row"><span>剩余保鲜期</span><strong>{{ assessResult.remaining_freshness_days }}天</strong></div>
              </div>
            </div>
            <div class="result-card">
              <div class="rc-title">📋 品质详情</div>
              <div class="rc-content">
                <div class="info-row"><span>品类</span><strong>{{ assessResult.product_type }}</strong></div>
                <div class="info-row"><span>标准保鲜期</span><strong>{{ assessResult.total_freshness_days }}天</strong></div>
              </div>
              <div class="recommendation-box" :class="{warn:assessResult.grade.includes('D')||assessResult.grade.includes('C')}">
                <strong>💡 建议：</strong>{{ assessResult.suggestion }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ 司机拍照审核（仓管审核） ============ -->
    <div class="section-block" v-show="activeTab === 'review'">
      <div class="section-header">
        <h3>📷 司机拍照审核</h3>
        <span class="card-badge badge-purple">功能 · 仓管审核</span>
        <div class="review-stats-inline" v-if="reviewStats">
          <span class="rsi-item rsi-pending">待审 {{ reviewStats.pending || 0 }}</span>
          <span class="rsi-item rsi-approved">已通过 {{ reviewStats.approved || 0 }}</span>
          <span class="rsi-item rsi-rejected">已驳回 {{ reviewStats.rejected || 0 }}</span>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <button class="btn btn-sm" :class="{ active: reviewFilter === 'pending_review' }" @click="reviewFilter = 'pending_review'; loadPendingReviews()">待审核</button>
          <button class="btn btn-sm" :class="{ active: reviewFilter === 'approved' }" @click="reviewFilter = 'approved'; loadPendingReviews()">已通过</button>
          <button class="btn btn-sm" :class="{ active: reviewFilter === 'rejected' }" @click="reviewFilter = 'rejected'; loadPendingReviews()">已驳回</button>
          <button class="btn btn-sm" :class="{ active: reviewFilter === 'all' }" @click="reviewFilter = 'all'; loadPendingReviews()">全部</button>
        </div>
        <div class="toolbar-right">
          <!-- 🔴 批量审核按钮 -->
          <template v-if="reviewFilter === 'pending_review' && reviewList.length > 0">
            <button class="btn btn-sm" @click="toggleSelectAll">
              {{ selectedReviewIds.length === reviewList.length ? '取消全选' : '全选' }}
            </button>
            <button class="btn btn-approve btn-sm" @click="batchReview('approve')" :disabled="selectedReviewIds.length === 0 || batchReviewing">
              {{ batchReviewing ? '审核中...' : `✅ 批量通过 (${selectedReviewIds.length})` }}
            </button>
            <button class="btn btn-reject btn-sm" @click="openBatchRejectDialog" :disabled="selectedReviewIds.length === 0">
              ❌ 批量驳回 ({{ selectedReviewIds.length }})
            </button>
          </template>
          <button class="btn btn-primary btn-sm" @click="loadPendingReviews" :disabled="reviewLoading">
            {{ reviewLoading ? '加载中...' : '刷新列表' }}
          </button>
        </div>
      </div>

      <!-- 审核列表 -->
      <div class="glass-card" v-if="reviewList.length > 0">
        <div class="review-grid">
          <div
            v-for="item in reviewList"
            :key="item.id"
            class="review-card"
            :class="'rev-' + item.review_status"
          >
            <div class="rev-check" v-if="item.review_status === 'pending_review'" @click.stop="toggleSelect(item.id)">
              <span class="rev-checkbox" :class="{ checked: selectedReviewIds.includes(item.id) }">
                {{ selectedReviewIds.includes(item.id) ? '✓' : '' }}
              </span>
            </div>
            <div class="rev-img-wrap">
              <img :src="item.url" :alt="item.original_name" class="rev-img" @click="previewImage = item.url" />
              <span class="rev-type-tag" :class="item.photo_type === 'accept' ? 'type-accept' : 'type-deliver'">
                {{ item.photo_type === 'accept' ? '🚛 出发' : '📦 送达' }}
              </span>
            </div>
            <div class="rev-info">
              <div class="rev-row"><span class="rev-label">订单</span><span class="rev-val">{{ item.order_id || item.waybill_id || '—' }}</span></div>
              <div class="rev-row"><span class="rev-label">设备</span><span class="rev-val">{{ item.device_id }}</span></div>
              <div class="rev-row"><span class="rev-label">时间</span><span class="rev-val">{{ formatRevTime(item.upload_time) }}</span></div>
              <div class="rev-row"><span class="rev-label">备注</span><span class="rev-val rev-notes">{{ item.notes || '—' }}</span></div>
              <div class="rev-row" v-if="item.review_status !== 'pending_review'">
                <span class="rev-label">审核</span>
                <span class="rev-val" :class="item.review_status === 'approved' ? 'text-teal' : 'text-red'">
                  {{ item.review_status === 'approved' ? '✅ 已通过' : '❌ 已驳回' }}
                </span>
              </div>
              <div class="rev-row" v-if="item.review_notes">
                <span class="rev-label">意见</span><span class="rev-val rev-notes">{{ item.review_notes }}</span>
              </div>
            </div>
            <!-- 待审核才显示操作按钮 -->
            <div class="rev-actions" v-if="item.review_status === 'pending_review'">
              <button class="btn btn-approve" @click="doReview(item, 'approve')">✅ 通过</button>
              <button class="btn btn-reject" @click="openRejectDialog(item)">❌ 驳回</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="glass-card" v-else>
        <div class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--border)" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          <p>暂无{{ reviewFilterText }}的拍照记录</p>
          <span>司机上传出发/送达照片后将显示在此处</span>
        </div>
      </div>

      <!-- 图片预览弹窗 -->
      <div class="photo-modal-overlay" v-if="previewImage" @click="previewImage = ''">
        <div class="photo-modal-box" @click.stop>
          <span class="pm-close" @click="previewImage = ''">✕</span>
          <img :src="previewImage" class="pm-img" />
        </div>
      </div>

      <!-- 驳回弹窗 -->
      <div class="photo-modal-overlay" v-if="rejectDialog.target" @click="rejectDialog.target = null">
        <div class="reject-dialog" @click.stop>
          <h4>驳回照片 — {{ rejectDialog.target.order_id || rejectDialog.target.waybill_id }}</h4>
          <p class="reject-tip">请填写驳回原因，司机将收到通知并重新拍照上传</p>
          <textarea v-model="rejectDialog.notes" placeholder="例如：照片模糊不清、未拍摄货物全貌、温度记录纸不可读..." rows="3" class="reject-textarea"></textarea>
          <div class="photo-actions">
            <button class="btn btn-cancel" @click="rejectDialog.target = null">取消</button>
            <button class="btn btn-reject" :disabled="!rejectDialog.notes.trim()" @click="confirmReject">确认驳回</button>
          </div>
        </div>
      </div>

      <!-- 🔴 批量驳回弹窗 -->
      <div class="photo-modal-overlay" v-if="batchRejectDialog.show" @click="batchRejectDialog.show = false">
        <div class="reject-dialog" @click.stop>
          <h4>批量驳回 — {{ selectedReviewIds.length }} 张照片</h4>
          <p class="reject-tip">请填写驳回原因，所有选中的照片将统一驳回</p>
          <textarea v-model="batchRejectDialog.notes" placeholder="例如：照片模糊不清、未拍摄货物全貌..." rows="3" class="reject-textarea"></textarea>
          <div class="photo-actions">
            <button class="btn btn-cancel" @click="batchRejectDialog.show = false">取消</button>
            <button class="btn btn-reject" :disabled="!batchRejectDialog.notes.trim()" @click="confirmBatchReject">确认批量驳回</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ 第二部分：冷机故障预测（功能4） ============ -->
    <div class="section-block" v-show="activeTab === 'maintenance'">
      <div class="section-header">
        <h3>冷机故障预测性维护</h3>
        <span class="card-badge badge-amber">功能4 · 预测性维护</span>
      </div>

      <!-- 设备统计 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon" style="background:var(--red-bg);color:var(--red)">⚠</div>
          <div class="stat-info">
            <div class="stat-value text-red">{{ maintStats.critical + maintStats.high }}</div>
            <div class="stat-label">高风险设备</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(245,158,11,0.12);color:var(--amber)">●</div>
          <div class="stat-info">
            <div class="stat-value text-amber">{{ maintStats.medium }}</div>
            <div class="stat-label">中风险设备</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(0,210,160,0.12);color:var(--teal)">✓</div>
          <div class="stat-info">
            <div class="stat-value text-teal">{{ maintStats.low }}</div>
            <div class="stat-label">正常运行</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(0,168,255,0.12);color:var(--accent)">📊</div>
          <div class="stat-info">
            <div class="stat-value">{{ maintStats.total }}</div>
            <div class="stat-label">监测设备总数</div>
          </div>
        </div>
      </div>

      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <button class="btn btn-sm" :class="{ active: filterRisk === '' }" @click="filterRisk = ''">全部</button>
          <button class="btn btn-sm" :class="{ active: filterRisk === 'critical' }" @click="filterRisk = 'critical'" style="color:var(--red)">紧急</button>
          <button class="btn btn-sm" :class="{ active: filterRisk === 'high' }" @click="filterRisk = 'high'" style="color:var(--red)">高风险</button>
          <button class="btn btn-sm" :class="{ active: filterRisk === 'medium' }" @click="filterRisk = 'medium'" style="color:var(--amber)">中风险</button>
          <button class="btn btn-sm" :class="{ active: filterRisk === 'low' }" @click="filterRisk = 'low'" style="color:var(--teal)">低风险</button>
        </div>
        <button class="btn btn-primary btn-sm" @click="refreshMaintenance" :disabled="maintLoading">
          {{ maintLoading ? '预测中...' : '刷新预测' }}
        </button>
      </div>

      <!-- 设备列表 -->
      <div class="glass-card">
        <div class="card-header">设备故障预测列表</div>
        <div v-if="maintLoading" class="loading-block">
          <div class="spinner"></div>
          <span>正在执行XGBoost模型推理...</span>
        </div>
        <div v-else class="device-table">
          <div class="table-header">
            <span class="col-id">设备ID</span>
            <span class="col-model">冷机型号</span>
            <span class="col-life">剩余寿命</span>
            <span class="col-prob">故障概率</span>
            <span class="col-risk">风险等级</span>
            <span class="col-type">预测故障</span>
            <span class="col-action">操作</span>
          </div>
          <div v-for="item in filteredDevices" :key="item.device_id" class="table-row" :class="'row-' + item.risk_level" @click="selectDevice(item)">
            <span class="col-id">{{ item.device_id }}</span>
            <span class="col-model">{{ item.unit_brand }} {{ item.unit_model }}</span>
            <span class="col-life">{{ item.remaining_life_days }}天</span>
            <span class="col-prob">
              <div class="prob-bar"><div class="prob-fill" :style="{ width: (item.failure_probability * 100) + '%', background: probColor(item.failure_probability) }"></div></div>
              <span>{{ (item.failure_probability * 100).toFixed(1) }}%</span>
            </span>
            <span class="col-risk"><span class="tag" :class="'tag-' + item.risk_level">{{ item.risk_label }}</span></span>
            <span class="col-type">{{ item.predicted_failure_type || '—' }}</span>
            <span class="col-action"><button class="btn-text" @click.stop="selectDevice(item)">详情</button></span>
          </div>
        </div>
      </div>

      <!-- 设备详情 -->
      <div class="glass-card" v-if="selectedDevice" style="margin-top:16px">
        <div class="card-header">设备详情 — {{ selectedDevice.device_id }}</div>
        <div class="detail-grid">
          <div class="dg-col">
            <h4>基本信息</h4>
            <div class="info-row"><span>冷机型号</span><strong>{{ selectedDevice.unit_brand }} {{ selectedDevice.unit_model }}</strong></div>
            <div class="info-row"><span>额定功率</span><strong>{{ selectedDevice.unit_power_kw }} kW</strong></div>
            <div class="info-row"><span>总寿命</span><strong>{{ selectedDevice.total_life_hours }}小时</strong></div>
            <div class="info-row"><span>已运行</span><strong>{{ selectedDevice.current_run_hours }}小时</strong></div>
            <div class="info-row"><span>剩余寿命</span><strong :class="lifeClass(selectedDevice.remaining_life_days)">{{ selectedDevice.remaining_life_days }}天</strong></div>
          </div>
          <div class="dg-col">
            <h4>实时运行参数</h4>
            <div class="info-row" v-for="(val, key) in selectedDevice.real_time_params" :key="key">
              <span>{{ (key as string).replace(/_/g, ' ') }}</span>
              <strong>{{ val }}</strong>
            </div>
          </div>
          <div class="dg-col">
            <h4>预测结果</h4>
            <div class="info-row"><span>故障概率</span><strong :style="{color:probColor(selectedDevice.failure_probability)}">{{ (selectedDevice.failure_probability * 100).toFixed(1) }}%</strong></div>
            <div class="info-row"><span>风险等级</span><strong>{{ selectedDevice.risk_label }}</strong></div>
            <div class="info-row"><span>预测故障类型</span><strong>{{ selectedDevice.predicted_failure_type || '暂无预测' }}</strong></div>
            <div class="info-row"><span>建议维护时间</span><strong>{{ selectedDevice.next_maintenance_label }} ({{ selectedDevice.next_maintenance_hours }}小时内)</strong></div>
            <hr>
            <h4>特征重要性分析</h4>
            <div class="info-row" v-for="(pct, name) in selectedDevice.feature_importance" :key="name">
              <span>{{ name }}</span>
              <strong>{{ pct }}%</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { qualityAPI, maintenanceAPI, uploadAPI, resourceAPI, customerAPI } from '@/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const store = useAppStore()

function statusLabel(s: string): string {
  const m: Record<string, string> = { pending: '待接单', accepted: '已接单', in_transit: '配送中', delivered: '已送达', completed: '已完成', cancelled: '已取消' }
  return m[s] || s
}

const currentDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${['日','一','二','三','四','五','六'][d.getDay()]}`
})

// ====== Tab 切换 ======
const activeTab = ref('overview')

// ====== 概览页数据 ======
const sparkData = reactive({
  inventory: '0,20 10,15 20,18 30,12 40,16 50,10 60,14 70,8 80,12',
  expiry: '0,18 10,16 20,14 30,15 40,12 50,10 60,8 70,6 80,4',
  review: '0,20 10,18 20,16 30,14 40,12 50,10 60,8 70,6 80,4',
  maint: '0,4 10,6 20,8 30,10 40,12 50,14 60,16 70,18 80,20',
})

const hasTodos = computed(() => {
  return (maintStats.value?.high_risk > 0) || (reviewStats.value?.pending > 0) ||
    (orderReviewStats.value?.pending > 0) || (invSummary.value?.data?.total_expired > 0)
})

const recentLogs = computed(() => {
  const logs: { time: string; tag: string; type: string; msg: string }[] = []
  const now = dayjs()
  if (reviewStats.value?.approved > 0) logs.push({ time: now.subtract(5, 'minute').format('HH:mm'), tag: '审核', type: 'success', msg: `通过 ${reviewStats.value.approved} 张拍照审核` })
  if (maintStats.value?.normal > 0) logs.push({ time: now.subtract(12, 'minute').format('HH:mm'), tag: '巡检', type: 'info', msg: `${maintStats.value.normal} 台冷机运行正常` })
  if (invSummary.value?.data?.total_kg > 0) logs.push({ time: now.subtract(30, 'minute').format('HH:mm'), tag: '库存', type: 'info', msg: `库存快照 ${invSummary.value.data.total_kg}kg` })
  if (orderReviewStats.value?.approved > 0) logs.push({ time: now.subtract(1, 'hour').format('HH:mm'), tag: '订单', type: 'success', msg: `审核通过 ${orderReviewStats.value.approved} 个订单` })
  if (logs.length === 0) {
    logs.push({ time: now.format('HH:mm'), tag: '系统', type: 'info', msg: '工作台已就绪，等待数据刷新' })
  }
  return logs
})

function refreshAll() {
  loadOrderReview()
  refreshInventory()
  loadQualityStats()
  loadPendingReviews()
  refreshMaintenance()
  ElMessage.success('数据已刷新')
}

// ====== 品质评估（功能7） ======
const uploadedImage = ref('')
const selectedFile = ref<File | null>(null)
const uploadInput = ref<HTMLInputElement | null>(null)
const assessing = ref(false)
const assessResult = ref<any>(null)
const qualityStats = ref<any>({})

const qualityStatsCards = computed(() => [
  { label: '批次总数', value: qualityStats.value.total_batches || 0, icon: '📦', bg: 'rgba(0,168,255,0.12)', color: 'var(--accent)' },
  { label: '瑕疵率', value: (qualityStats.value.defect_rate || 0) + '%', icon: '⚠', bg: 'var(--red-bg)', color: 'var(--red)' },
  { label: '平均品质评分', value: (qualityStats.value.avg_quality_score || 0), icon: '⭐', bg: 'rgba(0,210,160,0.12)', color: 'var(--teal)' },
  { label: '支持品类', value: qualityStats.value.products_supported || 0, icon: '🏷', bg: 'rgba(124,58,237,0.12)', color: 'var(--aurora)' },
])

function getGradeColor(grade: string) {
  if (!grade) return '#6b7280'
  if (grade.includes('S')) return 'linear-gradient(135deg, #00d2a0, #22c55e)'
  if (grade.includes('A')) return 'linear-gradient(135deg, #22c55e, #16a34a)'
  if (grade.includes('B')) return 'linear-gradient(135deg, #f59e0b, #d97706)'
  if (grade.includes('C')) return 'linear-gradient(135deg, #f97316, #ea580c)'
  return 'linear-gradient(135deg, #ef4444, #dc2626)'
}

function triggerUpload() { if (!assessing.value) uploadInput.value?.click() }
function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) loadFile(file)
}
function handleDrop(e: DragEvent) {
  const file = e.dataTransfer?.files[0]
  if (file && file.type.startsWith('image/')) loadFile(file)
}
function loadFile(file: File) {
  if (!file.type.startsWith('image/')) { ElMessage.warning('请上传图片文件'); return }
  if (file.size > 10 * 1024 * 1024) { ElMessage.warning('图片大小不能超过10MB'); return }
  selectedFile.value = file; assessResult.value = null
  const reader = new FileReader()
  reader.onload = (e) => { uploadedImage.value = e.target?.result as string; doAssess() }
  reader.readAsDataURL(file)
}
function clearUpload() {
  uploadedImage.value = ''; selectedFile.value = null; assessResult.value = null
  if (uploadInput.value) uploadInput.value.value = ''
}

async function doAssess() {
  assessing.value = true
  try {
    if (selectedFile.value) {
      const formData = new FormData()
      formData.append('file', selectedFile.value)
      formData.append('storage_days', '3')
      const res = await qualityAPI.assessWithImage(formData)
      assessResult.value = res.data || null
    }
  } catch { ElMessage.error('品质评估失败') }
  finally { assessing.value = false }
}

async function loadQualityStats() {
  try { const sRes = await qualityAPI.getStats(); qualityStats.value = sRes } catch {}
}

// ====== 冷机故障预测（功能4） ======
const maintLoading = ref(false)
const filterRisk = ref('')
const predictions = ref<any[]>([])
const selectedDevice = ref<any>(null)
const maintStats = ref({ total: 0, critical: 0, high: 0, medium: 0, low: 0 })

const filteredDevices = computed(() => {
  if (!filterRisk.value) return predictions.value
  return predictions.value.filter((p: any) => p.risk_level === filterRisk.value)
})

function probColor(p: number) {
  if (p > 0.65) return 'var(--red)'
  if (p > 0.4) return 'var(--amber)'
  if (p > 0.15) return 'var(--accent)'
  return 'var(--teal)'
}
function lifeClass(days: number) {
  if (days < 30) return 'text-red'
  if (days < 90) return 'text-amber'
  return 'text-teal'
}

async function refreshMaintenance() {
  maintLoading.value = true
  try {
    const res: any = await maintenanceAPI.predictAll(filterRisk.value || undefined)
    predictions.value = res.predictions || []
    maintStats.value.total = res.total_devices || 0
    maintStats.value.critical = res.summary?.critical_high || 0
    maintStats.value.high = res.summary?.critical_high || 0
    maintStats.value.medium = res.summary?.medium || 0
    maintStats.value.low = res.summary?.low || 0
  } catch { ElMessage.error('获取预测数据失败') }
  finally { maintLoading.value = false }
}

async function selectDevice(item: any) {
  try {
    const res: any = await maintenanceAPI.predictDevice(item.device_id)
    selectedDevice.value = res
  } catch { ElMessage.error('获取设备详情失败') }
}

// ====== 司机拍照审核 ======
const reviewLoading = ref(false)
const reviewFilter = ref('pending_review')
const reviewList = ref<any[]>([])
const reviewStats = ref<any>(null)
const previewImage = ref('')
const rejectDialog = reactive({ target: null as any, notes: '' })

const reviewFilterText = computed(() => {
  const map: Record<string, string> = { pending_review: '待审核', approved: '已通过', rejected: '已驳回', all: '' }
  return map[reviewFilter.value] || ''
})

function formatRevTime(t: string) {
  if (!t) return '—'
  return dayjs(t).format('MM-DD HH:mm:ss')
}

async function loadPendingReviews() {
  reviewLoading.value = true
  try {
    const res: any = await uploadAPI.getPendingReviews(reviewFilter.value, 50)
    reviewList.value = res.data?.records || res.records || []
  } catch { ElMessage.error('加载审核列表失败') }
  finally { reviewLoading.value = false }
}

async function loadReviewStats() {
  try {
    const res: any = await uploadAPI.getReviewStats()
    reviewStats.value = res.data || res
  } catch { /* ignore */ }
}

async function doReview(item: any, action: string) {
  try {
    await uploadAPI.reviewPhoto(item.id, action)
    // 审核通过后从待审核列表中移除，驳回后也移除（当前在 pending_review 筛选下）
    if (reviewFilter.value === 'pending_review') {
      reviewList.value = reviewList.value.filter((r: any) => r.id !== item.id)
    }
    ElMessage.success(action === 'approve' ? '审核通过！' : '已驳回')
    loadReviewStats()
  } catch (e: any) {
    console.error('审核失败详情:', JSON.stringify(e?.response?.data), 'status:', e?.response?.status)
    ElMessage.error('审核操作失败: ' + (e?.response?.data?.message || e?.response?.data?.detail || e?.message || '未知错误'))
  }
}

function openRejectDialog(item: any) {
  rejectDialog.target = item
  rejectDialog.notes = ''
}

async function confirmReject() {
  if (!rejectDialog.target || !rejectDialog.notes.trim()) return
  try {
    await uploadAPI.reviewPhoto(rejectDialog.target.id, 'reject', rejectDialog.notes.trim())
    // 驳回后从待审核列表中移除
    if (reviewFilter.value === 'pending_review') {
      reviewList.value = reviewList.value.filter((r: any) => r.id !== rejectDialog.target.id)
    }
    ElMessage.success('已驳回，司机将收到通知')
    rejectDialog.target = null
    rejectDialog.notes = ''
    loadReviewStats()
  } catch { ElMessage.error('驳回操作失败') }
}

// ====== 🔴 批量审核 ======
const selectedReviewIds = ref<string[]>([])
const batchReviewing = ref(false)
const batchRejectDialog = reactive({ show: false, notes: '' })

function toggleSelect(id: string) {
  const idx = selectedReviewIds.value.indexOf(id)
  if (idx >= 0) {
    selectedReviewIds.value.splice(idx, 1)
  } else {
    selectedReviewIds.value.push(id)
  }
}

function toggleSelectAll() {
  if (selectedReviewIds.value.length === reviewList.value.length) {
    selectedReviewIds.value = []
  } else {
    selectedReviewIds.value = reviewList.value.map((r: any) => r.id)
  }
}

async function batchReview(action: string) {
  if (selectedReviewIds.value.length === 0) {
    ElMessage.warning('请至少选择一条记录')
    return
  }
  batchReviewing.value = true
  try {
    const res: any = await uploadAPI.batchReview(selectedReviewIds.value, action)
    const cnt = res.success || 0
    ElMessage.success(`批量${action === 'approve' ? '通过' : '驳回'}完成：${cnt} 条成功`)
    selectedReviewIds.value = []
    loadPendingReviews()
    loadReviewStats()
  } catch (err: any) {
    ElMessage.error('批量操作失败: ' + (err?.response?.data?.detail || err?.message || '未知错误'))
  } finally {
    batchReviewing.value = false
  }
}

function openBatchRejectDialog() {
  if (selectedReviewIds.value.length === 0) {
    ElMessage.warning('请至少选择一条记录')
    return
  }
  batchRejectDialog.show = true
  batchRejectDialog.notes = ''
}

async function confirmBatchReject() {
  if (!batchRejectDialog.notes.trim()) return
  await batchReview('reject')
  batchRejectDialog.show = false
  batchRejectDialog.notes = ''
}

// ====== 仓库库存管理 ======
const invLoading = ref(false)
const invSummary = ref<any>(null)
const inventoryList = ref<any[]>([])
const warehouseList = ref<any[]>([])
const invFilter = reactive({ warehouse_id: '', zone: '', status: '', keyword: '' })
const inboundForm = reactive({ warehouse_id: '', zone: '', product_name: '', category: '', quantity_kg: 0, shelf_life_days: 30, target_temp_c: -18, notes: '' })
const inboundLoading = ref(false)
const outboundForm = reactive({ inventory_id: '', quantity_kg: 0, notes: '' })
const outboundLoading = ref(false)
const selectedInv = ref<any>(null)

async function loadWarehouses() {
  try {
    const res: any = await resourceAPI.getWarehouses()
    warehouseList.value = res.warehouses || []
  } catch { /* ignore */ }
}

async function loadInventorySummary() {
  try {
    const res: any = await resourceAPI.getWarehouseInventorySummary()
    invSummary.value = res
  } catch { /* ignore */ }
}

async function loadInventory() {
  invLoading.value = true
  try {
    const res: any = await resourceAPI.getWarehouseInventory(invFilter)
    inventoryList.value = res.data?.items || []
  } catch { /* ignore */ }
  finally { invLoading.value = false }
}

async function refreshInventory() {
  await Promise.all([loadInventorySummary(), loadInventory(), loadWarehouses()])
}

async function doInbound() {
  if (!inboundForm.warehouse_id || !inboundForm.zone || !inboundForm.product_name || inboundForm.quantity_kg <= 0) {
    ElMessage.warning('请填写完整入库信息')
    return
  }
  inboundLoading.value = true
  try {
    await resourceAPI.warehouseInbound({ ...inboundForm })
    ElMessage.success('入库成功！')
    inboundForm.product_name = ''; inboundForm.category = ''; inboundForm.quantity_kg = 0; inboundForm.notes = ''
    refreshInventory()
  } catch { ElMessage.error('入库失败') }
  finally { inboundLoading.value = false }
}

async function doOutbound() {
  if (!outboundForm.inventory_id || outboundForm.quantity_kg <= 0) {
    ElMessage.warning('请选择库存并填写出库数量')
    return
  }
  outboundLoading.value = true
  try {
    await resourceAPI.warehouseOutbound(outboundForm.inventory_id, outboundForm.quantity_kg, outboundForm.notes)
    ElMessage.success('出库成功！')
    outboundForm.inventory_id = ''; outboundForm.quantity_kg = 0; outboundForm.notes = ''; selectedInv.value = null
    refreshInventory()
  } catch { ElMessage.error('出库失败') }
  finally { outboundLoading.value = false }
}

function onOutboundSelect() {
  selectedInv.value = inventoryList.value.find(i => i.id === outboundForm.inventory_id) || null
}

// ====== 订单审核（新增） ======
const orderReviewLoading = ref(false)
const orderReviewFilter = ref('pending')
const orderReviewList = ref<any[]>([])
const orderReviewStats = ref<any>({ pending: 0, approved: 0, rejected: 0 })
const orderRejectDialog = reactive({ target: null as any, notes: '' })

const statusMap: Record<string, string> = {
  pending: '待接单',
  accepted: '已接单',
  loaded: '已装货',
  in_transit: '配送中',
  completed: '已完成',
}

const orderReviewFilterText = computed(() => {
  const map: Record<string, string> = { pending: '待审核', approved: '已通过', rejected: '已驳回', all: '' }
  return map[orderReviewFilter.value] || ''
})

function getZoneClass(zoneName: string): string {
  if (zoneName?.includes('冷冻')) return 'zone-freeze'
  if (zoneName?.includes('冷藏')) return 'zone-chill'
  return 'zone-ambient'
}

function formatOrderTime(t: string) {
  if (!t) return '—'
  return dayjs(t).format('MM-DD HH:mm')
}

async function loadOrderReview() {
  orderReviewLoading.value = true
  try {
    let res: any
    if (orderReviewFilter.value === 'pending') {
      res = await customerAPI.getPendingReviewOrders()
    } else if (orderReviewFilter.value === 'all') {
      res = await customerAPI.getAllReviewOrders()
    } else {
      res = await customerAPI.getAllReviewOrders(orderReviewFilter.value)
    }
    orderReviewList.value = res.orders || []

    // 计算统计
    const allRes: any = await customerAPI.getAllReviewOrders()
    const all = allRes.orders || []
    orderReviewStats.value = {
      pending: all.filter((o: any) => !o.review_status || o.review_status === 'pending').length,
      approved: all.filter((o: any) => o.review_status === 'approved').length,
      rejected: all.filter((o: any) => o.review_status === 'rejected').length,
    }
  } catch { /* ignore */ }
  finally { orderReviewLoading.value = false }
}

async function approveOrder(order: any) {
  try {
    await customerAPI.reviewOrder(order.order_id, 'approve', '审核通过')
    ElMessage.success(`订单 ${order.order_id} 审核通过！`)
    loadOrderReview()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  }
}

function openOrderRejectDialog(order: any) {
  orderRejectDialog.target = order
  orderRejectDialog.notes = ''
}

async function confirmOrderReject() {
  if (!orderRejectDialog.target || !orderRejectDialog.notes.trim()) return
  try {
    await customerAPI.reviewOrder(orderRejectDialog.target.order_id, 'reject', orderRejectDialog.notes.trim())
    ElMessage.success('订单已驳回')
    orderRejectDialog.target = null
    orderRejectDialog.notes = ''
    loadOrderReview()
  } catch { ElMessage.error('驳回操作失败') }
}

onMounted(() => {
  store.startAutoRefresh(8000)
  loadQualityStats()
  refreshMaintenance()
  loadPendingReviews()
  loadReviewStats()
  refreshInventory()
})

onUnmounted(() => {
  store.stopAutoRefresh()
})
</script>

<style scoped>
.warehouse-page { animation: fadeInUp 0.5s ease-out; }
.page-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  margin-bottom: 24px; padding-bottom: 18px;
  border-bottom: 1px solid var(--border-light);
}
.page-title { font-size: 22px; font-weight: 800; color: var(--text-title); margin: 0; font-family: var(--font-display); }
.page-subtitle { font-size: 13px; color: var(--text-muted); margin-left: 12px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.live-indicator { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--teal); font-family: var(--font-mono); font-weight: 500; }
.live-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--teal); animation: pulse-ring 2s ease-out infinite; box-shadow: 0 0 8px rgba(0,200,150,0.4); }
.date-display { font-size: 12px; color: var(--text-muted); background: var(--bg-input); padding: 5px 14px; border-radius: 20px; border: 1px solid var(--border-light); }

/* Section */
.section-block { margin-bottom: 28px; }
.section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-header h3 { font-size: 17px; font-weight: 700; color: var(--text-title); margin: 0; }
.card-badge { font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 20px; letter-spacing: 0.04em; }
.badge-green { background: var(--teal-bg); color: var(--teal); }
.badge-amber { background: var(--amber-bg); color: var(--amber); }

/* Stats */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 18px; }
.stat-card {
  display: flex; align-items: center; gap: 14px; padding: 18px 20px;
  background: var(--bg-card); border-radius: var(--radius-lg); border: 1px solid var(--border-card);
  box-shadow: var(--shadow-sm); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.stat-card:hover { box-shadow: var(--shadow); transform: translateY(-2px); border-color: var(--border-focus); }
.stat-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.stat-value { font-family: var(--font-display); font-size: 28px; font-weight: 800; line-height: 1; color: var(--text-title); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 3px; font-weight: 500; }

.text-red { color: var(--red) !important; }
.text-amber { color: var(--amber) !important; }
.text-teal { color: var(--teal) !important; }

/* Upload */
.glass-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 22px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 18px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.glass-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,152,255,0.1), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}
.glass-card:hover { box-shadow: var(--shadow); }
.glass-card:hover::before { opacity: 1; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; font-size: 15px; font-weight: 700; color: var(--text-title); }
.header-tip { font-size: 12px; color: var(--text-muted); font-weight: 400; }

.upload-area { width: 100%; height: 300px; border: 2px dashed var(--border); border-radius: 16px; cursor: pointer; position: relative; overflow: hidden; transition: all 0.35s; background: rgba(0,0,0,0.01); }
.upload-area:hover { border-color: var(--accent); background: rgba(0,152,255,0.02); box-shadow: 0 0 30px rgba(0,152,255,0.06); }
.hidden-input { position: absolute; width: 0; height: 0; opacity: 0; }
.upload-placeholder { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.upload-placeholder h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 14px 0 6px; }
.upload-placeholder p { font-size: 12px; color: var(--text-muted); margin: 0; }
.upload-icon-wrap { padding: 18px; }
.upload-preview { width: 100%; height: 100%; position: relative; }
.preview-img { width: 100%; height: 100%; object-fit: contain; background: rgba(0,0,0,0.02); }
.preview-overlay { position: absolute; bottom: 0; left: 0; right: 0; padding: 16px; background: linear-gradient(transparent, rgba(0,0,0,0.75)); }
.preview-status { color: #fff; font-size: 13px; font-weight: 500; }
.preview-close { position: absolute; top: 12px; right: 12px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.55); color: #fff; border-radius: 50%; font-size: 14px; cursor: pointer; transition: all 0.2s; }
.preview-close:hover { background: rgba(0,0,0,0.75); transform: scale(1.1); }
.assessing-loader { display: flex; align-items: center; gap: 10px; color: #fbbf24; font-size: 13px; font-weight: 500; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.loader-ring { width: 24px; height: 24px; border: 3px solid rgba(251,191,36,0.3); border-top-color: #fbbf24; border-radius: 50%; animation: spin 1s linear infinite; }

/* Result */
.result-section { margin-top: 18px; padding: 18px; background: rgba(0,0,0,0.015); border-radius: 14px; border: 1px solid var(--border-light); }
.grade-badge { display: flex; align-items: center; justify-content: center; gap: 14px; padding: 20px; border-radius: 14px; margin-bottom: 16px; }
.grade-text { font-family: var(--font-display); font-size: 44px; font-weight: 800; color: #fff; text-shadow: 0 2px 8px rgba(0,0,0,0.15); }
.grade-score { font-size: 20px; color: rgba(255,255,255,0.9); font-weight: 600; }
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.result-card { background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-card); overflow: hidden; box-shadow: var(--shadow-xs); }
.rc-title { padding: 12px 16px; font-size: 13px; font-weight: 700; color: var(--text-title); border-bottom: 1px solid var(--border-light); background: rgba(0,0,0,0.01); }
.rc-content { padding: 12px 16px; }
.info-row { display: flex; justify-content: space-between; padding: 5px 0; font-size: 12px; border-bottom: 1px solid rgba(0,0,0,0.02); }
.info-row span { color: var(--text-muted); }
.info-row strong { font-weight: 600; color: var(--text-primary); }
.recommendation-box { margin: 12px 16px 16px; padding: 12px 14px; border-radius: 10px; background: rgba(0,200,150,0.08); font-size: 12px; line-height: 1.5; border: 1px solid rgba(0,200,150,0.12); }
.recommendation-box.warn { background: var(--red-bg); border-color: rgba(239,68,68,0.12); }

/* Toolbar */
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.toolbar-left { display: flex; gap: 8px; }
.toolbar-right { display: flex; gap: 8px; align-items: center; }
.btn {
  border: 1px solid var(--border); background: var(--bg-card);
  color: var(--text-secondary); padding: 6px 14px; border-radius: 8px;
  cursor: pointer; font-size: 12px; font-weight: 600;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-bg); }
.btn.active { background: var(--accent-bg); border-color: var(--accent); color: var(--accent); font-weight: 700; box-shadow: 0 2px 8px rgba(0,152,255,0.12); }
.btn-primary { background: linear-gradient(135deg, var(--accent), #0078e8); color: #fff; border: none; box-shadow: 0 2px 12px rgba(0,152,255,0.25); }
.btn-primary:hover { box-shadow: 0 4px 18px rgba(0,152,255,0.4); color: #fff; background: linear-gradient(135deg, var(--accent), #0078e8); }
.btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-sm { padding: 5px 12px; font-size: 12px; }
.btn-text { color: var(--accent); border: none; background: none; cursor: pointer; font-size: 12px; font-weight: 600; }
.btn-text:hover { text-decoration: underline; }

/* Device Table */
.loading-block { display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 48px; color: var(--text-muted); }
.spinner { width: 32px; height: 32px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
.table-header { display: flex; padding: 12px 16px; font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; border-bottom: 2px solid var(--border); background: rgba(0,0,0,0.01); }
.table-row { display: flex; align-items: center; padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.03); cursor: pointer; transition: all 0.2s; font-size: 13px; }
.table-row:hover { background: var(--accent-bg); }
.table-row.row-critical { background: rgba(239,68,68,0.05); border-left: 3px solid var(--red); }
.table-row.row-high { background: rgba(245,158,11,0.03); border-left: 3px solid var(--amber); }
.col-id { width: 100px; font-family: var(--font-mono); font-size: 12px; font-weight: 600; }
.col-model { flex: 1; }
.col-life { width: 80px; }
.col-prob { width: 170px; display: flex; align-items: center; gap: 10px; }
.col-risk { width: 80px; }
.col-type { width: 130px; color: var(--text-muted); }
.col-action { width: 60px; }
.prob-bar { width: 80px; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.prob-fill { height: 100%; border-radius: 4px; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
.tag { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; }
.tag-critical { background: var(--red-bg); color: var(--red); }
.tag-high { background: rgba(245,158,11,0.12); color: var(--amber); }
.tag-medium { background: rgba(0,152,255,0.1); color: var(--accent); }
.tag-low { background: rgba(0,200,150,0.1); color: var(--teal); }

/* Detail */
.detail-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.dg-col { background: var(--bg-page); border-radius: 12px; padding: 18px; border: 1px solid var(--border-light); }
.dg-col h4 { font-size: 14px; margin-bottom: 10px; color: var(--text-title); font-weight: 700; }
.dg-col hr { border: none; border-top: 1px solid var(--border-light); margin: 12px 0; }

@media (max-width: 1200px) { .stats-row { grid-template-columns: repeat(2, 1fr); } .detail-grid { grid-template-columns: 1fr; } }
@media (max-width: 768px) { .stats-row { grid-template-columns: 1fr; } .result-grid { grid-template-columns: 1fr; } }

/* ====== 订单审核样式 ====== */
.order-review-list { display: flex; flex-direction: column; gap: 14px; }
.or-item {
  padding: 18px; border-radius: 14px; border: 1px solid var(--border-card);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--bg-card); box-shadow: var(--shadow-sm);
}
.or-item:hover { box-shadow: var(--shadow); transform: translateY(-1px); }
.or-item.or-pending { border-left: 4px solid var(--amber); }
.or-item.or-approved { border-left: 4px solid var(--teal); opacity: 0.9; }
.or-item.or-rejected { border-left: 4px solid var(--red); opacity: 0.8; }
.or-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.or-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.or-id { font-family: var(--font-mono); font-size: 14px; font-weight: 700; color: var(--text-title); }
.or-price { font-family: var(--font-display); font-size: 20px; font-weight: 800; color: var(--red); }
.or-status-tag {
  font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 12px;
  letter-spacing: 0.03em;
}
.or-status-tag.accepted { background: rgba(0,152,255,0.1); color: var(--accent); }
.or-status-tag.in_transit { background: rgba(124,58,237,0.1); color: var(--aurora); }
.or-review-tag {
  font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 12px;
  letter-spacing: 0.03em;
}
.or-review-tag.pending { background: rgba(245,158,11,0.12); color: var(--amber); }
.or-review-tag.approved { background: rgba(0,210,160,0.12); color: var(--teal); }
.or-review-tag.rejected { background: rgba(239,68,68,0.12); color: var(--red); }

.or-body { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.or-info-row { display: flex; gap: 10px; font-size: 12px; align-items: center; }
.or-label { color: var(--text-muted); min-width: 56px; flex-shrink: 0; font-weight: 600; }
.or-temp { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); }
.or-actions { display: flex; gap: 10px; justify-content: flex-end; padding-top: 10px; border-top: 1px solid var(--border); }
.text-accent { color: var(--accent); font-weight: 700; }
.text-teal { color: var(--teal); font-weight: 600; }
.text-red { color: var(--red) !important; }

/* Zone badges for order review */
.zone-badge { font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 6px; letter-spacing: 0.03em; }
.zone-freeze { background: rgba(59,130,246,0.12); color: #3b82f6; }
.zone-chill { background: rgba(16,185,129,0.12); color: #10b981; }
.zone-ambient { background: rgba(245,158,11,0.12); color: #f59e0b; }

/* ====== 拍照审核区域 ====== */
.badge-purple { background: rgba(124,58,237,0.12); color: var(--aurora); }
.review-stats-inline { display: flex; gap: 10px; margin-left: auto; }
.rsi-item {
  font-size: 11px; font-weight: 700; padding: 3px 12px; border-radius: 14px;
  font-family: var(--font-mono); letter-spacing: 0.03em;
}
.rsi-pending { background: rgba(245,158,11,0.12); color: var(--amber); }
.rsi-approved { background: rgba(0,210,160,0.12); color: var(--teal); }
.rsi-rejected { background: rgba(239,68,68,0.12); color: var(--red); }

.review-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }
.review-card {
  display: flex; gap: 16px; padding: 16px;
  border-radius: 14px; border: 1px solid var(--border-card);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--bg-card); box-shadow: var(--shadow-sm);
}
.review-card:hover { box-shadow: var(--shadow); transform: translateY(-2px); }
.review-card.rev-pending_review { border-left: 4px solid var(--amber); background: rgba(245,158,11,0.03); }
.review-card.rev-approved { border-left: 4px solid var(--teal); opacity: 0.9; }
.review-card.rev-rejected { border-left: 4px solid var(--red); opacity: 0.8; }
.rev-img-wrap {
  width: 150px; height: 112px; flex-shrink: 0;
  border-radius: 10px; overflow: hidden; position: relative;
  cursor: pointer; border: 1px solid var(--border);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.rev-img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.35s ease; }
.rev-img-wrap:hover .rev-img { transform: scale(1.08); }
.rev-img-wrap::after {
  content: '🔍'; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  font-size: 28px; opacity: 0; transition: opacity 0.3s ease; pointer-events: none;
}
.rev-img-wrap:hover::after { opacity: 0.9; }
.rev-type-tag {
  position: absolute; top: 8px; left: 8px;
  font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 6px;
  letter-spacing: 0.03em; box-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.type-accept { background: rgba(0,152,255,0.9); color: #fff; }
.type-deliver { background: rgba(0,200,150,0.9); color: #fff; }
.rev-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.rev-row { display: flex; gap: 8px; font-size: 12px; }
.rev-label { color: var(--text-muted); flex-shrink: 0; min-width: 36px; font-weight: 600; }
.rev-val { color: var(--text-title); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rev-notes { color: var(--text-secondary); font-size: 11px; line-height: 1.4; }
.rev-actions { display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; justify-content: center; }

/* 批量审核复选框 */
.rev-check { display: flex; align-items: center; padding-right: 4px; flex-shrink: 0; }
.rev-checkbox {
  width: 24px; height: 24px; border: 2px solid var(--border); border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #fff; cursor: pointer; transition: all 0.2s ease;
}
.rev-checkbox:hover { border-color: var(--accent); background: rgba(0,152,255,0.05); }
.rev-checkbox.checked { background: var(--accent); border-color: var(--accent); box-shadow: 0 2px 8px rgba(0,152,255,0.3); }
.btn-approve {
  background: linear-gradient(135deg, var(--teal), #00b080);
  color: #fff; border: none; padding: 7px 16px; border-radius: 8px;
  font-size: 12px; font-weight: 700; cursor: pointer;
  transition: all 0.2s ease; box-shadow: 0 2px 8px rgba(0,200,150,0.25);
}
.btn-approve:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,200,150,0.35); }
.btn-reject {
  background: linear-gradient(135deg, var(--red), #dc2626);
  color: #fff; border: none; padding: 7px 16px; border-radius: 8px;
  font-size: 12px; font-weight: 700; cursor: pointer;
  transition: all 0.2s ease; box-shadow: 0 2px 8px rgba(239,68,68,0.25);
}
.btn-reject:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(239,68,68,0.35); }

/* 图片预览弹窗 */
.photo-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.8);
  z-index: 3000; display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(8px); animation: fadeIn 0.2s ease;
}
.photo-modal-box { position: relative; max-width: 90vw; max-height: 90vh; animation: fadeInUp 0.3s ease; }
.pm-img { max-width: 90vw; max-height: 85vh; border-radius: 16px; object-fit: contain; box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
.pm-close {
  position: absolute; top: -16px; right: -16px; width: 40px; height: 40px;
  border-radius: 50%; background: var(--red); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; cursor: pointer; box-shadow: 0 4px 14px rgba(239,68,68,0.4);
  transition: all 0.2s ease;
}
.pm-close:hover { transform: scale(1.1); }

/* 驳回弹窗 */
.reject-dialog { background: var(--bg-card); border-radius: 16px; padding: 28px; width: 90%; max-width: 460px; box-shadow: var(--shadow-lg); }
.reject-dialog h4 { font-size: 18px; font-weight: 700; color: var(--text-title); margin-bottom: 8px; }
.reject-tip { font-size: 13px; color: var(--amber); margin-bottom: 16px; font-weight: 500; }
.reject-textarea {
  width: 100%; padding: 12px 14px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--bg-input); color: var(--text-primary); font-size: 13px;
  resize: vertical; font-family: inherit; margin-bottom: 16px;
  transition: all 0.25s ease;
}
.reject-textarea:focus { outline: none; border-color: var(--red); box-shadow: 0 0 0 3px rgba(239,68,68,0.1); }
.reject-textarea::placeholder { color: var(--text-muted); }
.photo-actions { display: flex; gap: 12px; justify-content: flex-end; }
.btn-cancel {
  background: var(--bg-input); color: var(--text-muted); border: 1px solid var(--border);
  padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600;
  transition: all 0.2s ease;
}
.btn-cancel:hover { background: var(--border); color: var(--text-secondary); }

/* ====== 仓库管理 Tab ====== */
.main-tabs {
  display: flex; gap: 6px; margin-bottom: 22px;
  background: var(--bg-input); border-radius: 12px; padding: 5px;
  flex-wrap: wrap; box-shadow: inset 0 1px 3px rgba(0,0,0,0.04);
}
.tab-btn {
  flex: 1; padding: 10px 20px; border: none; border-radius: 10px; cursor: pointer;
  font-size: 13px; font-weight: 600; color: var(--text-muted); background: transparent;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative; min-width: 80px;
}
.tab-btn:hover { color: var(--text-primary); background: rgba(255,255,255,0.4); }
.tab-btn.active {
  background: var(--bg-card); color: var(--accent);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,152,255,0.08);
}
.tab-panel { animation: fadeInUp 0.35s ease-out; }

.wh-summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.wh-summary-card {
  background: var(--bg-card); border: 1px solid var(--border-card);
  border-radius: 14px; padding: 18px;
  transition: all 0.3s ease; box-shadow: var(--shadow-sm);
}
.wh-summary-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.wh-summary-name { font-size: 14px; font-weight: 700; color: var(--text-title); margin-bottom: 4px; }
.wh-summary-loc { font-size: 11px; color: var(--text-muted); margin-bottom: 12px; display: flex; align-items: center; gap: 4px; }
.wh-summary-loc::before { content: '📍'; font-size: 11px; }
.wh-summary-bars { display: flex; flex-direction: column; gap: 8px; }
.wh-bar-row { display: flex; align-items: center; gap: 8px; font-size: 11px; }
.wh-bar-label { width: 32px; color: var(--text-muted); flex-shrink: 0; font-weight: 600; font-size: 10px; }
.wh-bar-bg { flex: 1; height: 8px; background: var(--bg-input); border-radius: 4px; overflow: hidden; }
.wh-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
.frozen-fill { background: linear-gradient(90deg, #0098ff, #00a8ff); box-shadow: 0 0 6px rgba(0,168,255,0.25); }
.refrig-fill { background: linear-gradient(90deg, #00c896, #00e0a8); box-shadow: 0 0 6px rgba(0,210,160,0.25); }
.amb-fill { background: linear-gradient(90deg, #f59e0b, #fbbf24); box-shadow: 0 0 6px rgba(245,158,11,0.25); }
.wh-bar-val { width: 52px; text-align: right; font-family: var(--font-mono); color: var(--text-secondary); flex-shrink: 0; font-size: 11px; font-weight: 600; }
.wh-summary-alerts { margin-top: 10px; display: flex; gap: 8px; }
.wh-tag { font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 12px; letter-spacing: 0.03em; }
.tag-near { background: rgba(245,158,11,0.12); color: var(--amber); }
.tag-expired { background: rgba(239,68,68,0.12); color: var(--red); }

/* 入库/出库表单 */
.op-form { display: flex; flex-direction: column; gap: 14px; }
.form-row { display: flex; flex-direction: column; gap: 5px; }
.form-row.split { flex-direction: row; gap: 12px; }
.form-half { flex: 1; display: flex; flex-direction: column; gap: 5px; }
.form-row label { font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.form-select, .form-input {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: 10px;
  background: var(--bg-input); color: var(--text-primary); font-size: 13px;
  font-family: inherit; transition: all 0.25s ease;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.03);
}
.form-select:hover, .form-input:hover { border-color: var(--accent); }
.form-select:focus, .form-input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(0,152,255,0.1); }
.form-select-sm { padding: 6px 12px; font-size: 12px; }
.form-input-sm { padding: 6px 12px; font-size: 12px; width: 150px; }
.inv-detail { background: var(--bg-page); border-radius: 10px; padding: 12px; border: 1px solid var(--border); }
.inv-detail-row { display: flex; justify-content: space-between; font-size: 12px; padding: 4px 0; }
.inv-detail-row span { color: var(--text-muted); }
.inv-detail-row strong { font-weight: 700; color: var(--text-title); }

/* 库存表格 */
.toolbar-right { display: flex; gap: 10px; align-items: center; }
.inv-table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid var(--border); }
.inv-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.inv-table th {
  text-align: left; padding: 12px 14px; font-size: 10px; font-weight: 700;
  color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em;
  border-bottom: 2px solid var(--border); white-space: nowrap;
  background: var(--bg-input);
}
.inv-table td { padding: 11px 14px; border-bottom: 1px solid rgba(0,0,0,0.04); color: var(--text-primary); }
.inv-table .mono { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }
.inv-table .num { font-family: var(--font-mono); text-align: right; font-weight: 600; }
.inv-table tr.row-near_expiry { background: rgba(245,158,11,0.05); }
.inv-table tr.row-expired { background: rgba(239,68,68,0.05); }
.inv-table tr.row-near_expiry td:first-child { border-left: 3px solid var(--amber); }
.inv-table tr.row-expired td:first-child { border-left: 3px solid var(--red); }
.inv-table tr:hover { background: rgba(0,152,255,0.04); }
.inv-status { font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 12px; letter-spacing: 0.03em; }
.status-normal { background: rgba(0,210,160,0.12); color: var(--teal); }
.status-near_expiry { background: rgba(245,158,11,0.12); color: var(--amber); }
.status-expired { background: rgba(239,68,68,0.12); color: var(--red); }

/* ====== 概览页样式 ====== */
.overview-kpi {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-bottom: 24px;
}
.ov-kpi-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 16px;
  padding: 22px 20px;
  display: flex; align-items: center; gap: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.ov-kpi-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 16px 16px 0 0; opacity: 0; transition: opacity 0.3s ease;
}
.ov-kpi-card:hover { transform: translateY(-4px); box-shadow: var(--shadow); }
.ov-kpi-card:hover::before { opacity: 1; }
.ov-kpi-card.blue-glow::before { background: linear-gradient(90deg, #0098ff, #00b4ff); }
.ov-kpi-card.blue-glow:hover { border-color: rgba(0,168,255,0.3); box-shadow: 0 6px 24px rgba(0,168,255,0.12); }
.ov-kpi-card.amber-glow::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.ov-kpi-card.amber-glow:hover { border-color: rgba(245,158,11,0.3); box-shadow: 0 6px 24px rgba(245,158,11,0.12); }
.ov-kpi-card.green-glow::before { background: linear-gradient(90deg, #00c896, #00e0a8); }
.ov-kpi-card.green-glow:hover { border-color: rgba(0,210,160,0.3); box-shadow: 0 6px 24px rgba(0,210,160,0.12); }
.ov-kpi-card.purple-glow::before { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
.ov-kpi-card.purple-glow:hover { border-color: rgba(124,58,237,0.3); box-shadow: 0 6px 24px rgba(124,58,237,0.12); }

.ovk-icon {
  font-size: 32px; flex-shrink: 0;
  width: 52px; height: 52px; display: flex; align-items: center; justify-content: center;
  border-radius: 14px;
}
.ov-kpi-card.blue-glow .ovk-icon { background: rgba(0,152,255,0.08); }
.ov-kpi-card.amber-glow .ovk-icon { background: rgba(245,158,11,0.08); }
.ov-kpi-card.green-glow .ovk-icon { background: rgba(0,200,150,0.08); }
.ov-kpi-card.purple-glow .ovk-icon { background: rgba(124,58,237,0.08); }
.ovk-body { flex: 1; }
.ovk-value { font-family: var(--font-display); font-size: 30px; font-weight: 800; color: var(--text-title); line-height: 1; }
.ovk-value small { font-size: 14px; font-weight: 500; color: var(--text-muted); margin-left: 4px; }
.ovk-label { font-size: 12px; color: var(--text-muted); margin-top: 5px; font-weight: 500; }
.ovk-spark { width: 64px; height: 28px; opacity: 0.6; }
.ovk-spark .spark-svg { width: 100%; height: 100%; }
.ovk-spark.warn { color: #f59e0b; }
.ovk-spark.success { color: var(--teal); }
.ovk-spark.danger { color: #ef4444; }

/* Overview Grid */
.ov-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

/* Water Levels */
.water-levels { display: flex; flex-direction: column; gap: 18px; margin-top: 8px; }
.wl-item { }
.wl-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.wl-name { font-size: 13px; font-weight: 700; color: var(--text-title); }
.wl-pct { font-size: 13px; font-family: var(--font-mono); color: var(--text-muted); font-weight: 600; }
.wl-bar-stacked {
  display: flex; height: 12px; border-radius: 6px; overflow: hidden;
  background: var(--bg-input); box-shadow: inset 0 1px 3px rgba(0,0,0,0.06);
}
.wl-seg { transition: flex 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
.wl-seg.frozen { background: linear-gradient(90deg, #0098ff, #00b4ff); box-shadow: 0 0 8px rgba(0,168,255,0.2); }
.wl-seg.chilled { background: linear-gradient(90deg, #0ea5e9, #38bdf8); box-shadow: 0 0 8px rgba(14,165,233,0.2); }
.wl-seg.ambient { background: linear-gradient(90deg, #f59e0b, #fbbf24); box-shadow: 0 0 8px rgba(245,158,11,0.2); }
.wl-footer { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-top: 6px; }
.wl-warn { color: var(--amber); font-weight: 700; }

/* Todo List */
.todo-list { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
.todo-item {
  display: flex; align-items: center; gap: 14px;
  padding: 16px; border-radius: 12px;
  background: var(--bg-input); transition: all 0.25s ease;
  border: 1px solid transparent;
}
.todo-item:hover { background: var(--bg-page); border-color: var(--border); box-shadow: var(--shadow-sm); }
.todo-item.urgent { border-left: 4px solid #ef4444; }
.todo-item.important { border-left: 4px solid #f59e0b; }
.todo-icon { font-size: 20px; flex-shrink: 0; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 10px; }
.todo-item.urgent .todo-icon { background: rgba(239,68,68,0.08); }
.todo-item.important .todo-icon { background: rgba(245,158,11,0.08); }
.todo-body { flex: 1; }
.todo-title { display: block; font-size: 13px; font-weight: 700; color: var(--text-title); }
.todo-desc { display: block; font-size: 11px; color: var(--text-muted); margin-top: 3px; }
.todo-empty { text-align: center; padding: 30px; color: var(--teal); font-size: 14px; font-weight: 600; }
.todo-empty::before { content: '✅ '; font-size: 24px; display: block; margin-bottom: 8px; }
.btn-danger { background: linear-gradient(135deg, #ef4444, #dc2626) !important; color: #fff !important; border: none !important; }
.btn-warn { background: linear-gradient(135deg, #f59e0b, #d97706) !important; color: #fff !important; border: none !important; }

/* Log Stream */
.log-stream { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; max-height: 320px; overflow-y: auto; }
.log-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 10px;
  font-size: 12px; background: var(--bg-input);
  transition: all 0.2s ease; border: 1px solid transparent;
}
.log-item:hover { background: var(--bg-page); border-color: var(--border); }
.log-time { font-family: var(--font-mono); color: var(--text-muted); font-size: 11px; min-width: 44px; }
.log-tag {
  font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 6px;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.log-tag.success { background: rgba(0,210,160,0.12); color: var(--teal); }
.log-tag.info { background: rgba(0,152,255,0.1); color: var(--accent); }
.log-tag.warn { background: rgba(245,158,11,0.12); color: var(--amber); }
.log-msg { color: var(--text-secondary); flex: 1; }
.log-empty { text-align: center; padding: 24px; color: var(--text-muted); font-size: 13px; }

/* 订单同步步骤 */
.order-sync-steps {
  display: flex; align-items: flex-start; gap: 12px;
  margin-top: 8px; flex-wrap: wrap;
}
.oss-step {
  flex: 1; min-width: 100px; text-align: center;
  padding: 14px 12px; border-radius: 12px;
  background: var(--bg-input); border: 1px solid var(--border);
  transition: all 0.3s ease;
}
.oss-step.active {
  background: var(--bg-card); border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(0,152,255,0.08);
}
.oss-step.done { border-color: var(--teal); background: rgba(0,200,150,0.04); }
.oss-icon { font-size: 22px; margin-bottom: 6px; display: block; }
.oss-title { font-size: 12px; font-weight: 700; color: var(--text-title); }
.oss-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; }
.oss-arrow { font-size: 18px; color: var(--text-muted); align-self: center; flex-shrink: 0; }


@media (max-width: 1200px) { .overview-kpi { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) {
  .overview-kpi { grid-template-columns: 1fr; }
  .ov-grid { grid-template-columns: 1fr; }
  .wh-summary-grid { grid-template-columns: 1fr; }
  .order-sync-steps { flex-direction: column; }
  .oss-arrow { transform: rotate(90deg); }
}

/* ====== 订单流转同步面板 ====== */
.order-sync-steps { display: flex; align-items: center; gap: 0; margin-top: 16px; padding: 8px 0; overflow-x: auto; }
.oss-step { display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 72px; opacity: 0.4; transition: all .3s; }
.oss-step.active { opacity: 1; }
.oss-icon { font-size: 22px; }
.oss-num { font-size: 22px; font-weight: 800; color: #1a1a2e; font-family: var(--font-display); }
.oss-label { font-size: 11px; color: #999; }
.oss-arrow { color: #ccc; font-size: 16px; padding: 0 4px; flex-shrink: 0; margin-bottom: 20px; }
.oss-recent { margin-top: 12px; border-top: 1px solid var(--border-light); padding-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.oss-recent-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 8px; background: #f9fafb; font-size: 12px; }
.ossr-status { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 8px; white-space: nowrap; }
.ossr-status.pending { background: #fef3c7; color: #d97706; }
.ossr-status.accepted { background: #dbeafe; color: #2563eb; }
.ossr-status.in_transit { background: #ede9fe; color: #7c3aed; }
.ossr-status.delivered { background: #fff7ed; color: #ea580c; }
.ossr-status.completed { background: #d1fae5; color: #059669; }
.ossr-id { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }
.ossr-cargo { color: var(--text-primary); font-weight: 600; }
.ossr-route { color: #999; flex: 1; }
.ossr-driver { font-size: 11px; color: var(--accent); }

/* Live Tag */
.live-tag { display: inline-block; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: #dc2626; color: #fff; vertical-align: middle; margin-left: 6px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .6; } }
</style>
