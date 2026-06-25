<script setup>
import { ref, computed, onMounted } from 'vue'
import { getApplications, getApplication } from '@/api/application'
import { cancelApplication, calcCancelFee } from '@/api/application'
import { updateParticipant, cancelParticipant, changeResponsible } from '@/api/participant'
import { ElMessage, ElMessageBox } from 'element-plus'

const applyNo = ref('')
const appInfo = ref(null)
const participants = ref([])
const editDialogVisible = ref(false)
const editForm = ref({})
const applyList = ref([])
const allApplications = ref([])
const applyLoading = ref(false)

// 加载申请列表
async function loadApplications() {
  applyLoading.value = true
  try {
    const data = await getApplications()
    allApplications.value = data
      .filter(a => a.status === '进行中')  // 只显示进行中的申请
      .map(a => ({
        value: a.apply_no,
        label: `${a.apply_no} - ${a.route_name} (${a.responsible_name})`,
        status: a.status,
      }))
    applyList.value = [...allApplications.value]
  } catch (e) {
    ElMessage.error('加载申请列表失败')
  } finally {
    applyLoading.value = false
  }
}

// 远程搜索过滤
function remoteMethod(query) {
  if (query) {
    applyLoading.value = true
    setTimeout(() => {
      applyLoading.value = false
      applyList.value = allApplications.value.filter(item =>
        item.value.toLowerCase().includes(query.toLowerCase()) ||
        item.label.toLowerCase().includes(query.toLowerCase())
      )
    }, 200)
  } else {
    applyList.value = [...allApplications.value]
  }
}

async function search() {
  if (!applyNo.value) return
  try {
    appInfo.value = await getApplication(applyNo.value)
    participants.value = appInfo.value.participants || []
  } catch (e) { appInfo.value = null; participants.value = [] }
}

onMounted(() => {
  loadApplications()
})

function openEdit(p) {
  editForm.value = { ...p }
  editDialogVisible.value = true
}

async function handleEdit() {
  try {
    await updateParticipant(editForm.value.id, editForm.value)
    ElMessage.success('参加者信息已更新')
    editDialogVisible.value = false
    search()
  } catch (e) { /* handled */ }
}

async function handleCancelParticipant(p) {
  try {
    await ElMessageBox.confirm(`确认取消参加者 "${p.name}" 的参加？`, '确认', { type: 'warning' })
    await cancelParticipant(p.id)
    ElMessage.success('参加者已取消')
    search()
  } catch (e) { /* handled */ }
}

async function handleCancelApply() {
  if (!appInfo.value) return
  try {
    await ElMessageBox.confirm('确认取消整个申请？此操作不可撤销。', '确认取消', { type: 'error' })
    await cancelApplication(appInfo.value.apply_no, {})
    ElMessage.success('申请已取消')
    // 清空显示的信息
    appInfo.value = null
    participants.value = []
    applyNo.value = ''
    // 重新加载申请列表
    loadApplications()
  } catch (e) { /* handled */ }
}
</script>

<template>
  <el-card>
    <template #header><span>申请变更/取消</span></template>

    <el-form :inline="true" style="margin-bottom: 16px">
      <el-form-item label="申请编号">
        <el-select
          v-model="applyNo"
          filterable
          remote
          :remote-method="remoteMethod"
          :loading="applyLoading"
          placeholder="请选择或搜索申请编号"
          style="width: 350px"
          clearable
          @change="search"
        >
          <el-option
            v-for="item in applyList"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="search">查询</el-button>
      </el-form-item>
    </el-form>

    <template v-if="appInfo">
      <el-descriptions :column="3" border style="margin-bottom: 20px">
        <el-descriptions-item label="申请编号">{{ appInfo.apply_no }}</el-descriptions-item>
        <el-descriptions-item label="旅游团">{{ appInfo.route_name }}</el-descriptions-item>
        <el-descriptions-item label="出发日期">{{ appInfo.departure_date }}</el-descriptions-item>
        <el-descriptions-item label="申请责任人">{{ appInfo.responsible_name }}（{{ appInfo.responsible_phone }}）</el-descriptions-item>
        <el-descriptions-item label="参加人数">{{ appInfo.adult_count }}大{{ appInfo.child_count }}小</el-descriptions-item>
        <el-descriptions-item label="已付金额">¥{{ appInfo.deposit?.toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="余款截止日期">
          <span :style="{ color: appInfo.balance_deadline && appInfo.balance_deadline < new Date().toISOString().split('T')[0] ? '#ff4d4f' : '' }">
            {{ appInfo.balance_deadline || '未设置' }}
          </span>
        </el-descriptions-item>
      </el-descriptions>

      <el-row :gutter="16">
        <el-col :span="14">
          <el-card shadow="never">
            <template #header><span>参加者信息变更</span></template>
            <el-table :data="participants" stripe size="small">
              <el-table-column prop="name" label="姓名" />
              <el-table-column label="类型" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.type === '大人' ? 'primary' : 'warning'" size="small">{{ row.type }}</el-tag>
                  <el-tag v-if="row.is_responsible" type="success" size="small" style="margin-left: 4px">责任人</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="openEdit(row)">修改</el-button>
                  <el-button v-if="!row.is_responsible" type="danger" link size="small" @click="handleCancelParticipant(row)">取消</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="10">
          <el-card shadow="never" style="border-color: #ffccc7">
            <template #header><span style="color: #ff4d4f">取消整个申请</span></template>
            <p style="font-size: 13px; color: #666; margin-bottom: 12px">
              取消申请后，将根据距出发天数扣除取消手续费，退还剩余金额。
            </p>
            <el-table :data="[
              { days: '30天以上', rate: '10%' },
              { days: '15~29天', rate: '30%' },
              { days: '7~14天', rate: '50%' },
              { days: '7天以内', rate: '100%（不退）' },
            ]" size="small" style="margin-bottom: 16px">
              <el-table-column prop="days" label="距出发天数" />
              <el-table-column prop="rate" label="手续费比例" />
            </el-table>
            <el-button type="danger" style="width: 100%" @click="handleCancelApply">确认取消申请</el-button>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </el-card>

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
      <el-form-item label="身份证号"><el-input v-model="editForm.idcard" /></el-form-item>
      <el-form-item label="电话"><el-input v-model="editForm.phone" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleEdit">保存修改</el-button>
    </template>
  </el-dialog>
</template>
