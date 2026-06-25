<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getApplications, getApplication } from '@/api/application'
import { getParticipants, addParticipant, updateParticipant, cancelParticipant, changeResponsible } from '@/api/participant'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const applyNo = ref(route.params.applyNo || '')
const appList = ref([])
const appInfo = ref(null)
const participants = ref([])
const loading = ref(false)

// 弹窗状态
const dialogVisible = ref(false)
const editDialogVisible = ref(false)
const respDialogVisible = ref(false)
const form = ref({ name: '', gender: '男', age: 30, idcard: '', type: '大人', phone: '' })
const editForm = ref({ id: 0, name: '', gender: '男', age: 30, idcard: '', type: '大人', phone: '' })
const newRespId = ref(null)

function validateParticipant(data) {
  if (!data.name || !data.name.trim()) { ElMessage.error('姓名不能为空'); return false }
  if (!data.gender || !['男', '女'].includes(data.gender)) { ElMessage.error('性别必须为男或女'); return false }
  if (!Number.isInteger(data.age) || data.age < 1) { ElMessage.error('年龄必须为正整数'); return false }
  if (!['大人', '小孩'].includes(data.type)) { ElMessage.error('类型必须为大人或小孩'); return false }
  if (data.idcard && (!/^\d{18}$/.test(data.idcard))) { ElMessage.error('身份证号须为18位数字'); return false }
  if (data.phone && (!/^\d{11}$/.test(data.phone))) { ElMessage.error('电话号码须为11位数字'); return false }
  return true
}

onMounted(async () => {
  // 加载申请列表供选择
  try {
    const apps = await getApplications()
    appList.value = apps.filter((a) => a.status === '进行中')  // 只显示进行中的申请
  } catch (e) { /* handled */ }
  // 如果 URL 带了参数，自动查询
  if (applyNo.value) loadDetail()
})

// 选择申请后自动加载
watch(applyNo, (val) => { if (val) loadDetail() })

async function loadDetail() {
  if (!applyNo.value) return
  loading.value = true
  try {
    appInfo.value = await getApplication(applyNo.value)
    participants.value = appInfo.value.participants || []
  } catch (e) { appInfo.value = null; participants.value = [] }
  finally { loading.value = false }
}

async function handleAdd() {
  if (!validateParticipant(form.value)) return
  try {
    await addParticipant(applyNo.value, form.value)
    ElMessage.success('参加者添加成功')
    dialogVisible.value = false
    form.value = { name: '', gender: '男', age: 30, idcard: '', type: '大人', phone: '' }
    loadDetail()
  } catch (e) { /* handled */ }
}

function openEdit(p) {
  editForm.value = { ...p }
  editDialogVisible.value = true
}

async function handleEdit() {
  if (!validateParticipant(editForm.value)) return
  try {
    await updateParticipant(editForm.value.id, editForm.value)
    ElMessage.success('参加者信息已更新')
    editDialogVisible.value = false
    loadDetail()
  } catch (e) { /* handled */ }
}

async function handleCancel(p) {
  try {
    await ElMessageBox.confirm(`确认取消参加者 "${p.name}" 的参加？`, '确认取消', { type: 'warning' })
    await cancelParticipant(p.id)
    ElMessage.success('参加者已取消')
    loadDetail()
  } catch (e) { /* handled */ }
}

function openChangeResp() {
  newRespId.value = null
  respDialogVisible.value = true
}

async function handleChangeResp() {
  if (!newRespId.value) { ElMessage.warning('请选择新责任人'); return }
  try {
    await changeResponsible(applyNo.value, { new_responsible_id: newRespId.value })
    ElMessage.success('申请责任人已变更')
    respDialogVisible.value = false
    loadDetail()
  } catch (e) { /* handled */ }
}

const adultParticipants = () => participants.value.filter((p) => p.type === '大人' && !p.is_responsible)

const activeParticipants = () => participants.value.filter((p) => p.status === '已录入')
const actualAdultCount = () => activeParticipants().filter((p) => p.type === '大人').length
const actualChildCount = () => activeParticipants().filter((p) => p.type === '小孩').length
const isCountMismatch = () => appInfo.value && (
  actualAdultCount() !== appInfo.value.adult_count || actualChildCount() !== appInfo.value.child_count
)
</script>

<template>
  <el-card v-loading="loading">
    <template #header><span>参加者信息管理</span></template>

    <!-- 选择申请 -->
    <el-form :inline="true" style="margin-bottom: 16px">
      <el-form-item label="选择申请">
        <el-select
          v-model="applyNo"
          placeholder="请选择或输入申请编号"
          filterable
          clearable
          style="width: 360px"
        >
          <el-option
            v-for="app in appList"
            :key="app.apply_no"
            :label="`${app.apply_no}  ${app.route_name}  ${app.responsible_name}`"
            :value="app.apply_no"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-input v-model="applyNo" placeholder="或手动输入编号" style="width: 200px" @keyup.enter="loadDetail" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadDetail">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 申请信息 -->
    <el-descriptions v-if="appInfo" :column="3" border style="margin-bottom: 16px">
      <el-descriptions-item label="申请编号">{{ appInfo.apply_no }}</el-descriptions-item>
      <el-descriptions-item label="旅游团">{{ appInfo.route_name }}</el-descriptions-item>
      <el-descriptions-item label="出发日期">{{ appInfo.departure_date }}</el-descriptions-item>
      <el-descriptions-item label="申请责任人">{{ appInfo.responsible_name }}（{{ appInfo.responsible_phone }}）</el-descriptions-item>
      <el-descriptions-item label="参加人数">
        <span>{{ appInfo.adult_count }}大{{ appInfo.child_count }}小</span>
        <template v-if="appInfo">
          <span style="margin: 0 6px; color: #999">→</span>
          <span :style="{ color: isCountMismatch() ? '#ff4d4f' : '#52c41a', fontWeight: 600 }">
            {{ actualAdultCount() }}大{{ actualChildCount() }}小（实际）
          </span>
          <el-tag v-if="isCountMismatch()" type="danger" size="small" style="margin-left: 6px">人数不一致</el-tag>
        </template>
      </el-descriptions-item>
      <el-descriptions-item label="订金">¥{{ appInfo.deposit?.toLocaleString() }}</el-descriptions-item>
      <el-descriptions-item label="余款截止日期">
        <span :style="{ color: appInfo.balance_deadline && appInfo.balance_deadline < new Date().toISOString().split('T')[0] ? '#ff4d4f' : '' }">
          {{ appInfo.balance_deadline || '未设置' }}
        </span>
      </el-descriptions-item>
    </el-descriptions>

    <el-alert
      v-if="appInfo && isCountMismatch()"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      申报人数（{{ appInfo.adult_count }}大{{ appInfo.child_count }}小）与实际参加者（{{ actualAdultCount() }}大{{ actualChildCount() }}小）不一致，请确认是否需要调整。
    </el-alert>

    <el-empty v-if="!appInfo && !loading" description="请先选择一个申请" />

    <!-- 参加者列表 -->
    <template v-if="appInfo">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
        <span style="font-weight: 600">参加者列表</span>
        <el-button type="primary" size="small" @click="dialogVisible = true">+ 添加参加者</el-button>
      </div>

      <el-table :data="participants" stripe>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="gender" label="性别" width="60" />
        <el-table-column prop="age" label="年龄" width="60" />
        <el-table-column prop="idcard" label="身份证号" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.type === '大人' ? 'primary' : 'warning'" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_responsible ? 'success' : 'info'" size="small">
              {{ row.is_responsible ? '申请责任人' : '已录入' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEdit(row)">修改</el-button>
            <el-button v-if="row.is_responsible" type="warning" link size="small" @click="openChangeResp">变更责任人</el-button>
            <el-button v-else type="danger" link size="small" @click="handleCancel(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </el-card>

  <!-- 添加参加者弹窗 -->
  <el-dialog v-model="dialogVisible" title="添加参加者" width="500px">
    <el-form label-width="80px">
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="性别"><el-select v-model="form.gender"><el-option label="男" value="男" /><el-option label="女" value="女" /></el-select></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="年龄"><el-input-number v-model="form.age" :min="1" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="类型"><el-select v-model="form.type"><el-option label="大人" value="大人" /><el-option label="小孩" value="小孩" /></el-select></el-form-item></el-col>
      </el-row>
      <el-form-item label="身份证号"><el-input v-model="form.idcard" maxlength="18" placeholder="18位身份证号" /></el-form-item>
      <el-form-item label="电话"><el-input v-model="form.phone" maxlength="11" placeholder="11位手机号" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleAdd">确认添加</el-button>
    </template>
  </el-dialog>

  <!-- 编辑参加者弹窗 -->
  <el-dialog v-model="editDialogVisible" title="修改参加者信息" width="500px">
    <el-form label-width="80px">
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="姓名"><el-input v-model="editForm.name" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="性别"><el-select v-model="editForm.gender"><el-option label="男" value="男" /><el-option label="女" value="女" /></el-select></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="年龄"><el-input-number v-model="editForm.age" :min="1" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="类型"><el-select v-model="editForm.type"><el-option label="大人" value="大人" /><el-option label="小孩" value="小孩" /></el-select></el-form-item></el-col>
      </el-row>
      <el-form-item label="身份证号"><el-input v-model="editForm.idcard" maxlength="18" placeholder="18位身份证号" /></el-form-item>
      <el-form-item label="电话"><el-input v-model="editForm.phone" maxlength="11" placeholder="11位手机号" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleEdit">保存修改</el-button>
    </template>
  </el-dialog>

  <!-- 变更责任人弹窗 -->
  <el-dialog v-model="respDialogVisible" title="变更申请责任人" width="400px">
    <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
      只能从已录入的成人参加者中选择新的申请责任人。
    </el-alert>
    <el-select v-model="newRespId" placeholder="请选择新责任人" style="width: 100%">
      <el-option v-for="p in adultParticipants()" :key="p.id" :label="`${p.name}（${p.type}）`" :value="p.id" />
    </el-select>
    <template #footer>
      <el-button @click="respDialogVisible = false">取消</el-button>
      <el-button type="warning" @click="handleChangeResp">确认变更</el-button>
    </template>
  </el-dialog>
</template>
