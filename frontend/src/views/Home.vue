<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStats } from '@/api/finance'
import { getApplications } from '@/api/application'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const role = userStore.role
const stats = ref({ monthly_applications: 0, today_applications: 0, pending_balance: 0, upcoming_groups: 0 })
const applications = ref([])
const pendingList = ref([])

const canViewApplications = ['receptionist', 'collector', 'accountant', 'admin'].includes(role)
const canViewPendingBalance = ['collector', 'admin'].includes(role)

onMounted(async () => {
  const tasks = [getStats()]
  if (canViewApplications) tasks.push(getApplications())
  if (canViewPendingBalance) tasks.push(request.get('/api/pending-balance'))

  const results = await Promise.allSettled(tasks)

  if (results[0].status === 'fulfilled') stats.value = results[0].value

  let idx = 1
  if (canViewApplications && results[idx]) {
    if (results[idx].status === 'fulfilled') {
      const today = new Date().toISOString().split('T')[0]
      applications.value = results[idx].value
        .filter(a => !(a.status === '进行中' && a.departure_date < today))
        .slice(0, 5)
    }
    idx++
  }
  if (canViewPendingBalance && results[idx]) {
    if (results[idx].status === 'fulfilled') {
      const today = new Date().toISOString().split('T')[0]
      pendingList.value = results[idx].value.filter(p => p.balance_deadline >= today).slice(0, 5)
    }
  }
})

const statusType = (s) => ({ '进行中': 'primary', '已完成': 'success', '已取消': 'info' }[s] || 'info')
</script>

<template>
  <div>
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="router.push('/apply')">
          <div class="num" style="color: #1890ff">{{ stats.monthly_applications }}</div>
          <div class="label">本月申请数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="num" style="color: #fa8c16">{{ stats.today_applications }}</div>
          <div class="label">今日新增申请</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="router.push('/balance')">
          <div class="num" style="color: #ff4d4f">{{ stats.pending_balance }}</div>
          <div class="label">待处理余款</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="router.push('/tour-query')">
          <div class="num" style="color: #52c41a">{{ stats.upcoming_groups }}</div>
          <div class="label">即将出发旅游团</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="canViewApplications ? 16 : 24">
        <el-card v-if="canViewApplications">
          <template #header><span>最近申请记录</span></template>
          <el-table :data="applications" stripe size="small">
            <el-table-column prop="apply_no" label="申请编号" width="160" />
            <el-table-column prop="route_name" label="旅游团" />
            <el-table-column prop="departure_date" label="出发日期" width="110" />
            <el-table-column prop="responsible_name" label="申请责任人" width="100" />
            <el-table-column label="参加人数" width="90">
              <template #default="{ row }">{{ row.adult_count }}大{{ row.child_count }}小</template>
            </el-table-column>
            <el-table-column label="订金" width="100">
              <template #default="{ row }">¥{{ row.deposit?.toLocaleString() }}</template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="router.push(`/participant/${row.apply_no}`)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="canViewApplications ? 8 : 24">
        <el-card>
          <template #header><span>待办事项</span></template>
          <div style="display: flex; flex-direction: column; gap: 12px">
            <div v-for="item in [
              { text: '待处理余款支付', count: stats.pending_balance, path: '/balance' },
              { text: '即将出发旅游团', count: stats.upcoming_groups, path: '/tour-query' },
            ]" :key="item.text" class="todo-item" @click="router.push(item.path)">
              <span>{{ item.text }}</span>
              <el-badge :value="item.count" :max="99" />
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 16px" v-if="pendingList.length > 0">
          <template #header>
            <span style="color: #ff4d4f">⚠️ 余款即将到期</span>
          </template>
          <div style="display: flex; flex-direction: column; gap: 10px">
            <div v-for="item in pendingList" :key="item.apply_no" class="pending-item"
                 @click="router.push(`/participant/${item.apply_no}`)">
              <div style="font-weight: 500">{{ item.apply_no }}</div>
              <div style="font-size: 12px; color: #666">{{ item.route_name }}</div>
              <div style="font-size: 12px; color: #ff4d4f">
                截止: {{ item.balance_deadline }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-card { cursor: pointer; text-align: center; }
.stat-card .num { font-size: 28px; font-weight: 600; }
.stat-card .label { font-size: 13px; color: #999; margin-top: 6px; }
.todo-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid #f0f0f0; cursor: pointer; font-size: 13px;
}
.todo-item:hover { color: #1890ff; }
.pending-item {
  padding: 8px;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  cursor: pointer;
  background: #fff2f0;
}
.pending-item:hover { background: #ffece8; }
</style>
