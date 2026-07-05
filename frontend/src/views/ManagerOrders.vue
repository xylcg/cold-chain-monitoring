<template>
  <div class="manager-orders">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">订单管理中心</h2>
        <span class="page-subtitle">创建运单 · 调度分配 · 司机消息</span>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog = true">新建订单</el-button>
        <el-button @click="loadAllData" :loading="loading">刷新数据</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="order-tabs">
      <el-tab-pane name="all"><template #label>全部订单 <el-badge :value="waybills.length" class="tab-badge" /></template></el-tab-pane>
      <el-tab-pane name="pending"><template #label>待调度 <el-badge :value="pendingOrders.length" class="tab-badge" type="warning" /></template></el-tab-pane>
      <el-tab-pane name="transit"><template #label>运输中 <el-badge :value="transitOrders.length" class="tab-badge" type="primary" /></template></el-tab-pane>
      <el-tab-pane name="messages"><template #label>司机消息 <el-badge v-if="unreadMessages" :value="unreadMessages" class="tab-badge" type="danger" /></template></el-tab-pane>
    </el-tabs>

    <!-- 订单列表 -->
    <div v-if="activeTab !== 'messages'" class="glass-card">
      <div class="table-toolbar">
        <el-input v-model="searchKeyword" placeholder="搜索运单号/货物..." style="width:280px" clearable />
        <el-select v-model="filterCategory" placeholder="货物类别" clearable style="width:140px">
          <el-option label="冷冻食品" value="冷冻食品" />
          <el-option label="冷藏生鲜" value="冷藏生鲜" />
          <el-option label="疫苗医药" value="疫苗医药" />
          <el-option label="水果" value="水果" />
          <el-option label="蔬菜" value="蔬菜" />
        </el-select>
        <span class="toolbar-count">共 {{ filteredWaybills.length }} 条</span>
      </div>
      <el-table :data="paginatedWaybills" stripe max-height="500">
        <el-table-column prop="waybill_id" label="运单号" width="160"><template #default="{ row }"><code class="cell-code">{{ row.waybill_id }}</code></template></el-table-column>
        <el-table-column prop="cargo_name" label="货物名称" width="130" />
        <el-table-column prop="cargo_category" label="类别" width="100"><template #default="{ row }"><span class="cat-tag">{{ row.cargo_category }}</span></template></el-table-column>
        <el-table-column label="数量" width="90"><template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template></el-table-column>
        <el-table-column prop="origin" label="出发地" width="130" />
        <el-table-column prop="destination" label="目的地" width="130" />
        <el-table-column prop="status" label="状态" width="90"><template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="driver_name" label="司机" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="160"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="viewDetail(row)">详情</el-button>
            <el-button v-if="row.status==='pending'" text type="success" size="small" @click="assignToDriver(row)">分配</el-button>
            <el-button v-if="row.status==='pending'" text type="danger" size="small" @click="cancelOrder(row)">取消</el-button>
            <el-button v-if="row.status==='accepted'||row.status==='in_transit'" text type="warning" size="small" @click="sendDriverMsg(row)">消息</el-button>
            <el-button v-if="row.status==='accepted'||row.status==='in_transit'" text type="info" size="small" @click="openTempTrack(row)">🌡</el-button>
            <el-button v-if="row.status==='accepted'||row.status==='in_transit'" text type="info" size="small" @click="router.push('/tracking')">📍</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-pagination"><el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="filteredWaybills.length" layout="prev,pager,next" background small /></div>
    </div>

    <!-- 司机消息 -->
    <div v-if="activeTab === 'messages'" class="glass-card">
      <div class="msg-header"><h3>司机消息列表</h3><el-button text type="primary" size="small" @click="markAllRead" v-if="unreadMessages">全部已读</el-button></div>
      <div class="msg-list" v-if="driverMessages.length">
        <div v-for="msg in driverMessages" :key="msg.id" class="msg-item" :class="{ unread: !msg.read }" @click="msg.read = true">
          <div class="msg-avatar" :class="msg.severity==='urgent'?'urgent':''">{{ msg.from_name?.[0] || '司' }}</div>
          <div class="msg-body">
            <div class="msg-top"><span class="msg-from">{{ msg.from_name }}</span><span v-if="msg.severity==='urgent'" class="urgent-tag">紧急</span><span class="msg-time">{{ formatTime(msg.timestamp) }}</span></div>
            <div class="msg-title">{{ msg.title }}</div>
            <div class="msg-preview">{{ msg.content }}</div>
          </div>
          <div class="msg-actions"><el-button text type="primary" size="small" @click.stop="replyMessage(msg)">回复</el-button></div>
        </div>
      </div>
      <div v-else class="empty-state">暂无司机消息</div>
    </div>

    <!-- 新建订单弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建冷链订单" width="560px" destroy-on-close>
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="货物名称" required><el-input v-model="createForm.cargo_name" placeholder="如 进口车厘子" /></el-form-item>
        <el-form-item label="货物类别"><el-select v-model="createForm.cargo_category" style="width:100%"><el-option v-for="c in cargoTypes" :key="c" :label="c" :value="c" /></el-select></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="数量"><el-input-number v-model="createForm.quantity" :min="0" :max="50000" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="单位"><el-select v-model="createForm.unit" style="width:100%"><el-option label="kg" value="kg" /><el-option label="吨" value="吨" /><el-option label="箱" value="箱" /></el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="温度要求"><el-select v-model="createForm.temperature_requirement" style="width:100%"><el-option label="-25℃ ~ -18℃ (深冻)" value="-25℃ ~ -18℃" /><el-option label="-18℃ ~ -15℃ (冷冻)" value="-18℃ ~ -15℃" /><el-option label="0℃ ~ 4℃ (冷藏)" value="0℃ ~ 4℃" /><el-option label="2℃ ~ 8℃ (冷鲜)" value="2℃ ~ 8℃" /><el-option label="15℃ ~ 25℃ (恒温)" value="15℃ ~ 25℃" /></el-select></el-form-item>
        <el-form-item label="温区"><el-select v-model="createForm.zone_name" style="width:100%"><el-option label="冷冻区" value="冷冻区" /><el-option label="冷藏区" value="冷藏区" /><el-option label="恒温区" value="恒温区" /></el-select></el-form-item>
        <el-form-item label="出发地"><el-input v-model="createForm.origin" placeholder="如 华北中心冷库" /></el-form-item>
        <el-form-item label="目的地"><el-input v-model="createForm.destination" placeholder="如 北京市朝阳区" /></el-form-item>
        <el-form-item label="收货方"><el-input v-model="createForm.receiver" /></el-form-item>
        <el-form-item label="收货电话"><el-input v-model="createForm.receiver_phone" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="createForm.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreateDialog=false">取消</el-button><el-button type="primary" @click="submitCreate" :loading="creating">确认创建</el-button></template>
    </el-dialog>

    <!-- 分配司机弹窗 -->
    <el-dialog v-model="showAssignDialog" title="分配司机" width="480px" destroy-on-close>
      <div class="assign-info"><div class="assign-row"><span class="assign-label">运单号：</span><code>{{ assignTarget?.waybill_id }}</code></div><div class="assign-row"><span class="assign-label">货物：</span>{{ assignTarget?.cargo_name }}</div><div class="assign-row"><span class="assign-label">路线：</span>{{ assignTarget?.origin }} → {{ assignTarget?.destination }}</div></div>
      <el-form label-width="80px" style="margin-top:16px">
        <el-form-item label="选择司机"><el-select v-model="assignDriverId" style="width:100%" placeholder="请选择司机"><el-option v-for="d in driverList" :key="d.id" :label="`${d.name} (${d.plate})`" :value="d.id" /></el-select></el-form-item>
        <el-form-item label="车辆"><el-select v-model="assignVehicle" style="width:100%" placeholder="选择车辆"><el-option v-for="v in vehicleList" :key="v.id" :label="`${v.plate} — ${v.model}`" :value="v.id" /></el-select></el-form-item>
        <el-form-item label="备注"><el-input v-model="assignNote" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showAssignDialog=false">取消</el-button><el-button type="primary" @click="confirmAssign" :loading="assigning">确认分配</el-button></template>
    </el-dialog>

    <!-- 发消息弹窗 -->
    <el-dialog v-model="showMsgDialog" title="发送消息给司机" width="480px" destroy-on-close>
      <div class="assign-info"><div class="assign-row"><span class="assign-label">运单号：</span><code>{{ msgTarget?.waybill_id }}</code></div><div class="assign-row"><span class="assign-label">司机：</span>{{ msgTarget?.driver_name || '未分配' }}</div></div>
      <el-form label-width="80px" style="margin-top:16px">
        <el-form-item label="标题"><el-input v-model="msgTitle" placeholder="如：路线调整通知" /></el-form-item>
        <el-form-item label="紧急程度"><el-radio-group v-model="msgSeverity"><el-radio value="normal">普通</el-radio><el-radio value="urgent">紧急</el-radio></el-radio-group></el-form-item>
        <el-form-item label="内容"><el-input v-model="msgContent" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showMsgDialog=false">取消</el-button><el-button type="primary" @click="confirmSendMsg" :loading="sending">发送消息</el-button></template>
    </el-dialog>

    <!-- 回复弹窗 -->
    <el-dialog v-model="showReplyDialog" title="回复司机" width="480px" destroy-on-close>
      <div class="assign-info" v-if="replyTarget"><div class="assign-row"><span class="assign-label">来自：</span>{{ replyTarget.from_name }}</div><div class="assign-row"><span class="assign-label">原消息：</span>{{ replyTarget.content }}</div></div>
      <el-form label-width="80px" style="margin-top:16px"><el-form-item label="回复内容"><el-input v-model="replyContent" type="textarea" :rows="3" /></el-form-item></el-form>
      <template #footer><el-button @click="showReplyDialog=false">取消</el-button><el-button type="primary" @click="confirmReply">发送回复</el-button></template>
    </el-dialog>

    <!-- 温度追踪弹窗 -->
    <el-dialog v-model="showTempDialog" title="🌡 实时温度追踪" width="500px" destroy-on-close>
      <div v-if="tempLoading" style="text-align:center;padding:30px;color:#999">加载中...</div>
      <div v-else-if="tempTrackingData" class="temp-track-detail">
        <div class="tt-grid">
          <div class="tt-cell"><span>车牌号</span><strong>{{ tempTrackingData.vehicle?.plate_number || '—' }}</strong></div>
          <div class="tt-cell"><span>位置</span><strong>{{ tempTrackingData.vehicle?.current_city || '—' }}</strong></div>
          <div class="tt-cell"><span>当前温度</span><strong :class="{ danger: !tempTrackingData.temperature?.is_compliant }">{{ tempTrackingData.temperature?.current?.toFixed(1) }}℃</strong></div>
          <div class="tt-cell"><span>目标温度</span><strong>{{ tempTrackingData.waybill_info?.temperature_range || '—' }}</strong></div>
          <div class="tt-cell"><span>湿度</span><strong>{{ tempTrackingData.temperature?.humidity?.toFixed(1) }}%</strong></div>
          <div class="tt-cell"><span>冷机健康</span><strong :class="{ danger: (tempTrackingData.cold_car?.health||100) < 70 }">{{ tempTrackingData.cold_car?.health || 100 }}%</strong></div>
        </div>
        <div class="tt-status" :class="{ danger: !tempTrackingData.temperature?.is_compliant }">
          {{ tempTrackingData.temperature?.is_compliant ? '✅ 温度合规' : '⚠️ 温度异常 · 偏差 ' + (tempTrackingData.temperature?.deviation?.toFixed(1)||0) + '℃' }}
        </div>
      </div>
      <div v-else style="text-align:center;padding:30px;color:#999">暂无温度数据</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { traceabilityAPI, vehicleAPI, customerAPI } from '@/api'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const assigning = ref(false)
const sending = ref(false)
const activeTab = ref('all')
const searchKeyword = ref('')
const filterCategory = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const waybills = ref<any[]>([])
const driverMessages = ref<any[]>([])

const cargoTypes = ['冷冻食品','冷冻肉类','冷冻海鲜','冷藏生鲜','冷藏鲜奶','水果','蔬菜','疫苗医药','生物试剂','恒温药品','鲜花','其他']

const showCreateDialog = ref(false)
const createForm = ref({ cargo_name: '', cargo_category: '冷链', origin: '', destination: '', quantity: 1000, unit: 'kg', temperature_requirement: '-18℃ ~ -15℃', zone_name: '冷冻区', receiver: '', receiver_phone: '', notes: '' })

const showAssignDialog = ref(false)
const assignTarget = ref<any>(null)
const assignDriverId = ref('')
const assignVehicle = ref('')
const assignNote = ref('')

const driverList = ref([
  { id: 'driver01', name: '张司机', plate: '冷A-12345' },
  { id: 'driver02', name: '李司机', plate: '冷A-12346' },
  { id: 'driver03', name: '王司机', plate: '冷A-12347' },
  { id: 'driver04', name: '赵司机', plate: '冷A-12348' },
  { id: 'driver05', name: '孙司机', plate: '冷A-12349' },
])
const vehicleList = ref<any[]>([])

const showMsgDialog = ref(false)
const msgTarget = ref<any>(null)
const msgTitle = ref('')
const msgContent = ref('')
const msgSeverity = ref('normal')

const showReplyDialog = ref(false)
const replyTarget = ref<any>(null)
const replyContent = ref('')

// 统一状态机: pending(待接单)/accepted(已分配)/in_transit(运输中)/delivered(已送达)/completed(已完成)
const pendingOrders = computed(() => waybills.value.filter(w => w.status === 'pending'))
const transitOrders = computed(() => waybills.value.filter(w => w.status === 'accepted' || w.status === 'in_transit'))
const unreadMessages = computed(() => driverMessages.value.filter(m => !m.read).length)

const displayWaybills = computed(() => {
  if (activeTab.value === 'pending') return pendingOrders.value
  if (activeTab.value === 'transit') return transitOrders.value
  return waybills.value
})
const filteredWaybills = computed(() => {
  let list = displayWaybills.value
  if (searchKeyword.value) { const kw = searchKeyword.value.toLowerCase(); list = list.filter(w => w.waybill_id.toLowerCase().includes(kw) || w.cargo_name.toLowerCase().includes(kw) || (w.origin||'').toLowerCase().includes(kw) || (w.destination||'').toLowerCase().includes(kw)) }
  if (filterCategory.value) list = list.filter(w => w.cargo_category === filterCategory.value)
  return list
})
const paginatedWaybills = computed(() => {
  const s = (currentPage.value - 1) * pageSize.value
  return filteredWaybills.value.slice(s, s + pageSize.value)
})

// 统一状态机标签
function statusType(s: string): string { const m: Record<string,string> = { pending:'info', accepted:'warning', in_transit:'primary', delivered:'success', completed:'success', cancelled:'danger' }; return m[s]||'info' }
function statusLabel(s: string): string { const m: Record<string,string> = { pending:'待接单', accepted:'已分配', in_transit:'运输中', delivered:'已送达', completed:'已完成', cancelled:'已取消' }; return m[s]||s }
function formatTime(ts: string): string { if(!ts) return '—'; try { return new Date(ts).toLocaleString('zh-CN') } catch { return ts } }

async function loadAllData() {
  loading.value = true
  try {
    // 使用统一合并端点（来自 traceability，已合并 customer+world_state）
    const data: any = await traceabilityAPI.getWaybills()
    waybills.value = (data.waybills || []).map((w: any) => ({
      ...w,
      status: w.status || 'pending',
      driver_name: w.driver_name || '',
      driver_id: w.driver_id || '',
      vehicle_id: w.vehicle_id || '',
    }))
  } catch { waybills.value = [] }
  try {
    const vd: any = await vehicleAPI.getList()
    if (vd?.vehicles) vehicleList.value = vd.vehicles.map((v: any) => ({ id: v.device_id || v.id, plate: v.plate || v.device_id, model: v.model || '冷藏车' }))
  } catch {}
  loading.value = false
}

async function submitCreate() {
  if (!createForm.value.cargo_name) { ElMessage.warning('请填写货物名称'); return }
  creating.value = true
  try {
    // 使用 customer 订单创建 API（统一入口）
    await customerAPI.createOrder(createForm.value)
    ElMessage.success('订单创建成功！')
    showCreateDialog.value = false
    createForm.value = { cargo_name: '', cargo_category: '冷链', origin: '', destination: '', quantity: 1000, unit: 'kg', temperature_requirement: '-18℃ ~ -15℃', zone_name: '冷冻区', receiver: '', receiver_phone: '', notes: '' }
    await loadAllData()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '创建失败') }
  creating.value = false
}

function assignToDriver(row: any) { assignTarget.value = row; assignDriverId.value = ''; assignVehicle.value = ''; assignNote.value = ''; showAssignDialog.value = true }

async function confirmAssign() {
  if (!assignDriverId.value) { ElMessage.warning('请选择司机'); return }
  assigning.value = true
  try {
    const d = driverList.value.find(x => x.id === assignDriverId.value)
    const orderId = assignTarget.value?.waybill_id || assignTarget.value?.order_id
    // 调用后端 API 持久化分配
    await customerAPI.adminAssignDriver(orderId, {
      driver_id: assignDriverId.value,
      driver_name: d?.name || '',
      vehicle_id: assignVehicle.value,
      notes: assignNote.value,
    })
    ElMessage.success('订单已分配给司机！')
    showAssignDialog.value = false
    await loadAllData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '分配失败')
  }
  assigning.value = false
}

async function cancelOrder(row: any) {
  try {
    await ElMessageBox.confirm(`确定取消运单 ${row.waybill_id}？\n取消后订单将标记为已取消状态。`, '确认取消', { type: 'warning', confirmButtonText: '确认取消', cancelButtonText: '返回' })
    await customerAPI.deleteOrder(row.waybill_id)
    ElMessage.success('订单已取消')
    await loadAllData()
  } catch (e: any) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e?.response?.data?.detail || '取消失败')
    }
  }
}

function viewDetail(row: any) {
  ElMessageBox.alert(`运单号: ${row.waybill_id}\n货物: ${row.cargo_name}\n类别: ${row.cargo_category}\n数量: ${row.quantity} ${row.unit}\n出发地: ${row.origin||'—'}\n目的地: ${row.destination||'—'}\n状态: ${statusLabel(row.status)}\n司机: ${row.driver_name||'未分配'}\n创建时间: ${formatTime(row.created_at)}`, '运单详情', { confirmButtonText: '关闭' })
}

function sendDriverMsg(row: any) { msgTarget.value = row; msgTitle.value = ''; msgContent.value = ''; msgSeverity.value = 'normal'; showMsgDialog.value = true }

async function confirmSendMsg() {
  if (!msgContent.value) { ElMessage.warning('请输入消息内容'); return }
  sending.value = true
  driverMessages.value.unshift({ id: `msg-${Date.now()}`, from_name: '我（经理）', to_name: msgTarget.value?.driver_name || '司机', title: msgTitle.value || '订单调整通知', content: msgContent.value, timestamp: new Date().toISOString(), severity: msgSeverity.value, read: true, direction: 'outgoing', waybill_id: msgTarget.value?.waybill_id })
  ElMessage.success('消息已发送！')
  showMsgDialog.value = false
  sending.value = false
}

function replyMessage(msg: any) { replyTarget.value = msg; replyContent.value = ''; showReplyDialog.value = true }

function confirmReply() {
  if (!replyContent.value) { ElMessage.warning('请输入回复内容'); return }
  driverMessages.value.unshift({ id: `msg-${Date.now()}`, from_name: '我（经理）', to_name: replyTarget.value?.from_name, title: `回复: ${replyTarget.value?.title}`, content: replyContent.value, timestamp: new Date().toISOString(), severity: 'normal', read: true, direction: 'outgoing' })
  replyTarget.value.read = true; ElMessage.success('回复已发送！'); showReplyDialog.value = false
}

function markAllRead() { driverMessages.value.forEach(m => m.read = true) }

// ===== 温度追踪弹窗 =====
const showTempDialog = ref(false)
const tempTrackingData = ref<any>(null)
const tempLoading = ref(false)

async function openTempTrack(row: any) {
  showTempDialog.value = true
  tempTrackingData.value = null
  tempLoading.value = true
  try {
    const res: any = await customerAPI.getOrderTracking(row.waybill_id)
    if (res.status === 'ok') tempTrackingData.value = res.tracking
  } catch { ElMessage.warning('获取温度数据失败') }
  tempLoading.value = false
}

function initMockMessages() {
  driverMessages.value = [
    { id: 'm1', from_name: '张司机', title: '温度异常报告', content: '经理，车辆冷A-12345制冷温度偏高，当前6.2°C，请求指示是否继续配送？', timestamp: new Date(Date.now() - 1800000).toISOString(), severity: 'urgent', read: false, direction: 'incoming', waybill_id: 'WB20260528001' },
    { id: 'm2', from_name: '李司机', title: '配送完成确认', content: '运单WB20260528002已送达，客户已签收。全程温度正常，记录纸已上传。', timestamp: new Date(Date.now() - 3600000).toISOString(), severity: 'normal', read: false, direction: 'incoming', waybill_id: 'WB20260528002' },
    { id: 'm3', from_name: '王司机', title: '路线变更申请', content: 'G2京沪高速济南段因施工封路，请求绕行G3京台高速，预计增加30分钟。请批准。', timestamp: new Date(Date.now() - 7200000).toISOString(), severity: 'urgent', read: true, direction: 'incoming', waybill_id: 'WB20260528003' },
    { id: 'm4', from_name: '赵司机', title: '车辆故障报告', content: '车辆冷A-12348冷机异响，已停在服务区检查。请求维修支援。', timestamp: new Date(Date.now() - 9000000).toISOString(), severity: 'urgent', read: true, direction: 'incoming', waybill_id: '' },
  ]
}

onMounted(() => { loadAllData(); initMockMessages() })
</script>

<style scoped>
.manager-orders { display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; }
.page-title { font-size: 24px; font-weight: 700; color: #fff; margin: 0; }
.page-subtitle { font-size: 13px; color: rgba(255,255,255,0.45); margin-left: 12px; }
.header-left { display: flex; align-items: baseline; gap: 4px; }
.header-right { display: flex; gap: 8px; }

.order-tabs { margin-top: 4px; }
.tab-badge { margin-left: 6px; }

.glass-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 20px; }

.table-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.toolbar-count { font-size: 13px; color: rgba(255,255,255,0.4); margin-left: auto; }

.cell-code { font-family: var(--font-mono, 'JetBrains Mono', monospace); font-size: 12px; color: var(--accent); background: rgba(0,168,255,0.08); padding: 2px 6px; border-radius: 4px; }
.cat-tag { font-size: 12px; color: rgba(255,255,255,0.55); background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 4px; }

.table-pagination { display: flex; justify-content: flex-end; margin-top: 14px; }

.msg-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.msg-header h3 { margin: 0; font-size: 16px; color: #fff; font-weight: 600; }

.msg-list { display: flex; flex-direction: column; gap: 8px; }
.msg-item { display: flex; align-items: flex-start; gap: 12px; padding: 14px; border-radius: 10px; background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.04); cursor: pointer; transition: all 0.2s; }
.msg-item:hover { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.08); }
.msg-item.unread { background: rgba(0,168,255,0.04); border-color: rgba(0,168,255,0.12); }
.msg-avatar { width: 36px; height: 36px; border-radius: 10px; background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.6); font-size: 14px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.msg-avatar.urgent { background: rgba(239,68,68,0.15); color: #ef4444; }
.msg-body { flex: 1; min-width: 0; }
.msg-top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.msg-from { font-size: 13px; font-weight: 600; color: #fff; }
.msg-time { font-size: 11px; color: rgba(255,255,255,0.35); margin-left: auto; }
.msg-title { font-size: 13px; color: rgba(255,255,255,0.7); margin-bottom: 4px; }
.msg-preview { font-size: 12px; color: rgba(255,255,255,0.4); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 500px; }
.msg-actions { flex-shrink: 0; }
.urgent-tag { font-size: 10px; font-weight: 600; color: #ef4444; background: rgba(239,68,68,0.12); padding: 1px 6px; border-radius: 3px; }

.empty-state { text-align: center; padding: 60px 0; color: rgba(255,255,255,0.3); font-size: 14px; }

.assign-info { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 12px 16px; }
.assign-row { font-size: 13px; color: rgba(255,255,255,0.6); line-height: 1.8; }
.assign-label { color: rgba(255,255,255,0.35); margin-right: 4px; }
.assign-row code { font-family: var(--font-mono, monospace); color: var(--accent); font-size: 12px; }

/* 温度追踪 */
.temp-track-detail { display: flex; flex-direction: column; gap: 12px; }
.tt-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.tt-cell { padding: 10px 12px; border-radius: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; gap: 3px; }
.tt-cell span { font-size: 10px; color: rgba(255,255,255,0.4); }
.tt-cell strong { font-size: 14px; color: #fff; font-weight: 600; }
.tt-cell strong.danger { color: #ef4444; }
.tt-status { padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; text-align: center; background: rgba(0,210,160,0.1); color: #00d2a0; border: 1px solid rgba(0,210,160,0.15); }
.tt-status.danger { background: rgba(239,68,68,0.1); color: #ef4444; border-color: rgba(239,68,68,0.15); }
</style>
