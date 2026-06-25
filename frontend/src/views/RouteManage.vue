<script setup>
import { ref, onMounted } from 'vue'
import { getRoutes, getRoute, createRoute, updateRoute, cancelRoute } from '@/api/route'
import { ElMessage, ElMessageBox } from 'element-plus'

const routes = ref([])
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const editDialogVisible = ref(false)
const form = ref({ route_code: '', route_name: '', description: '' })
const editForm = ref({ route_code: '', route_name: '', description: '' })
const viewData = ref(null)

onMounted(async () => {
  try { routes.value = await getRoutes() } catch (e) { /* handled */ }
})

async function handleCreate() {
  try {
    await createRoute(form.value)
    ElMessage.success('路线创建成功')
    dialogVisible.value = false
    routes.value = await getRoutes()
  } catch (e) { /* handled */ }
}

async function handleView(code) {
  try {
    viewData.value = await getRoute(code)
    viewDialogVisible.value = true
  } catch (e) { /* handled */ }
}

function openEdit(r) {
  editForm.value = { route_code: r.route_code, route_name: r.route_name, description: r.description }
  editDialogVisible.value = true
}

async function handleEdit() {
  try {
    await updateRoute(editForm.value.route_code, editForm.value)
    ElMessage.success('路线更新成功')
    editDialogVisible.value = false
    routes.value = await getRoutes()
  } catch (e) { /* handled */ }
}

async function handleCancel(code) {
  try {
    await ElMessageBox.confirm(`确认取消旅游路线 ${code}？`, '确认取消', { type: 'warning' })
    await cancelRoute(code, {})
    ElMessage.success('路线已取消')
    routes.value = await getRoutes()
  } catch (e) { /* handled */ }
}
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span>旅游路线管理</span>
        <el-button type="primary" @click="dialogVisible = true">+ 新增旅游路线</el-button>
      </div>
    </template>

    <el-table :data="routes" stripe>
      <el-table-column prop="route_code" label="路线代码" width="100" />
      <el-table-column prop="route_name" label="路线名称" />
      <el-table-column prop="description" label="路线描述" show-overflow-tooltip />
      <el-table-column prop="created_date" label="创建日期" width="110" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === '活跃' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="handleView(row.route_code)">查看</el-button>
          <el-button v-if="row.status === '活跃'" type="warning" link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.status === '活跃'" type="danger" link size="small" @click="handleCancel(row.route_code)">取消</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <!-- 新增路线 -->
  <el-dialog v-model="dialogVisible" title="新增旅游路线" width="500px">
    <el-form label-width="80px">
      <el-form-item label="路线代码"><el-input v-model="form.route_code" placeholder="如 R-007" /></el-form-item>
      <el-form-item label="路线名称"><el-input v-model="form.route_name" placeholder="请输入路线名称" /></el-form-item>
      <el-form-item label="路线描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleCreate">创建路线</el-button>
    </template>
  </el-dialog>

  <!-- 查看路线详情 -->
  <el-dialog v-model="viewDialogVisible" title="旅游路线详情" width="600px">
    <template v-if="viewData">
      <el-descriptions :column="2" border style="margin-bottom: 16px">
        <el-descriptions-item label="路线代码">{{ viewData.route_code }}</el-descriptions-item>
        <el-descriptions-item label="路线名称">{{ viewData.route_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="viewData.status === '活跃' ? 'success' : 'info'" size="small">{{ viewData.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ viewData.description }}</el-descriptions-item>
      </el-descriptions>
      <h4 style="margin-bottom: 8px">包含的旅游活动</h4>
      <el-table :data="viewData.activities || []" size="small" style="margin-bottom: 16px">
        <el-table-column prop="activity_code" label="活动代码" width="100" />
        <el-table-column prop="activity_name" label="活动名称" />
        <el-table-column prop="description" label="描述" />
      </el-table>
      <h4 style="margin-bottom: 8px">变更历史</h4>
      <el-table :data="viewData.change_logs || []" size="small">
        <el-table-column prop="change_date" label="日期" width="110" />
        <el-table-column prop="content" label="变更内容" />
        <el-table-column prop="operator" label="操作人" width="80" />
      </el-table>
    </template>
  </el-dialog>

  <!-- 编辑路线 -->
  <el-dialog v-model="editDialogVisible" title="编辑旅游路线" width="500px">
    <el-form label-width="80px">
      <el-form-item label="路线代码"><el-input v-model="editForm.route_code" disabled /></el-form-item>
      <el-form-item label="路线名称"><el-input v-model="editForm.route_name" /></el-form-item>
      <el-form-item label="路线描述"><el-input v-model="editForm.description" type="textarea" :rows="3" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleEdit">保存修改</el-button>
    </template>
  </el-dialog>
</template>
