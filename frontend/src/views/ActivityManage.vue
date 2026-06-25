<script setup>
import { ref, onMounted } from 'vue'
import { getActivities, createActivity, updateActivity } from '@/api/activity'
import { getGroups, createGroup } from '@/api/group'
import { getRoutes } from '@/api/route'
import { ElMessage } from 'element-plus'

const activities = ref([])
const groups = ref([])
const routes = ref([])
const actDialogVisible = ref(false)
const grpDialogVisible = ref(false)
const actForm = ref({ activity_code: '', activity_name: '', description: '', route_code: '' })
const grpForm = ref({ group_code: '', activity_code: '', departure_date: '', deadline: '', capacity: 30 })

const nextActivityCode = ref('A-001')

onMounted(async () => {
  try {
    const [a, g, r] = await Promise.all([getActivities(), getGroups(), getRoutes()])
    activities.value = a
    groups.value = g
    routes.value = r

    if (a.length > 0) {
      const codes = a.map(item => {
        const num = parseInt(item.activity_code.replace('A-', ''))
        return isNaN(num) ? 0 : num
      })
      const maxNum = Math.max(...codes)
      nextActivityCode.value = `A-${String(maxNum + 1).padStart(3, '0')}`
    }
    actForm.value.activity_code = nextActivityCode.value
  } catch (e) { /* handled */ }
})

async function handleCreateActivity() {
  try {
    await createActivity(actForm.value)
    ElMessage.success('旅游活动创建成功')
    actDialogVisible.value = false
    activities.value = await getActivities()
  } catch (e) { /* handled */ }
}

async function handleCreateGroup() {
  try {
    await createGroup(grpForm.value)
    ElMessage.success('旅游团创建成功')
    grpDialogVisible.value = false
    groups.value = await getGroups()
  } catch (e) { /* handled */ }
}
</script>

<template>
  <el-card style="margin-bottom: 16px">
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span>旅游活动管理</span>
        <el-button type="primary" size="small" @click="actDialogVisible = true">+ 新增旅游活动</el-button>
      </div>
    </template>
    <el-table :data="activities" stripe size="small">
      <el-table-column prop="activity_code" label="活动代码" width="100" />
      <el-table-column prop="activity_name" label="活动名称" />
      <el-table-column prop="route_name" label="所属路线" />
      <el-table-column prop="description" label="活动描述" show-overflow-tooltip />
    </el-table>
  </el-card>

  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span>旅游团管理</span>
        <el-button type="primary" size="small" @click="grpDialogVisible = true">+ 创建旅游团</el-button>
      </div>
    </template>
    <el-table :data="groups" stripe size="small">
      <el-table-column prop="group_code" label="团代码" width="140" />
      <el-table-column prop="activity_name" label="所属活动" />
      <el-table-column prop="departure_date" label="出发日期" width="110" />
      <el-table-column prop="deadline" label="截止日期" width="110" />
      <el-table-column prop="capacity" label="人数限额" width="90" />
      <el-table-column prop="current_count" label="已报名" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '已开放' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <!-- 新增活动 -->
  <el-dialog v-model="actDialogVisible" title="新增旅游活动" width="500px">
    <el-form label-width="80px">
      <el-form-item label="活动代码">
        <el-select v-model="actForm.activity_code" filterable allow-create style="width: 100%" placeholder="选择或输入活动代码">
          <el-option :label="nextActivityCode + ' (自动生成)'" :value="nextActivityCode" />
          <el-divider v-if="activities.length > 0" style="margin: 4px 0" />
          <el-option v-for="a in activities" :key="a.activity_code" :label="a.activity_code + ' ' + a.activity_name" :value="a.activity_code" disabled />
        </el-select>
      </el-form-item>
      <el-form-item label="活动名称"><el-input v-model="actForm.activity_name" /></el-form-item>
      <el-form-item label="所属路线">
        <el-select v-model="actForm.route_code" style="width: 100%">
          <el-option v-for="r in routes" :key="r.route_code" :label="`${r.route_code} ${r.route_name}`" :value="r.route_code" />
        </el-select>
      </el-form-item>
      <el-form-item label="活动描述"><el-input v-model="actForm.description" type="textarea" :rows="3" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="actDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleCreateActivity">创建活动</el-button>
    </template>
  </el-dialog>

  <!-- 创建旅游团 -->
  <el-dialog v-model="grpDialogVisible" title="创建旅游团" width="500px">
    <el-form label-width="100px">
      <el-form-item label="团代码"><el-input v-model="grpForm.group_code" placeholder="如 YN-20260901" /></el-form-item>
      <el-form-item label="所属活动">
        <el-select v-model="grpForm.activity_code" style="width: 100%">
          <el-option v-for="a in activities" :key="a.activity_code" :label="`${a.activity_code} ${a.activity_name}`" :value="a.activity_code" />
        </el-select>
      </el-form-item>
      <el-form-item label="出发日期">
        <el-date-picker v-model="grpForm.departure_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
      </el-form-item>
      <el-form-item label="报名截止日期">
        <el-date-picker v-model="grpForm.deadline" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
      </el-form-item>
      <el-form-item label="人数限额">
        <el-input-number v-model="grpForm.capacity" :min="1" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="grpDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleCreateGroup">创建旅游团</el-button>
    </template>
  </el-dialog>
</template>
