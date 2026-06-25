<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getGroups } from '@/api/group'

const router = useRouter()
const groups = ref([])
const search = ref({ dest: '', date: '', status: '' })

onMounted(async () => {
  try { groups.value = await getGroups() } catch (e) { /* handled */ }
})

const today = new Date().toISOString().slice(0, 10)

function getEffectiveStatus(row) {
  // 后端状态优先：未开放、已完成、已取消
  if (['未开放', '已完成', '已取消'].includes(row.status)) return row.status
  // 已满员
  if (row.current_count >= row.capacity) return '已满员'
  // 已过截止日期
  if (row.deadline && row.deadline < today) return '已截止'
  // 已过出发日期
  if (row.departure_date && row.departure_date < today) return '已出发'
  return '已开放'
}

function canApply(row) {
  return getEffectiveStatus(row) === '已开放'
}

const filtered = computed(() => {
  return groups.value.filter((g) => {
    const matchDest = !search.value.dest || g.route_name?.includes(search.value.dest)
    const matchDate = !search.value.date || g.departure_date === search.value.date
    const effectiveStatus = getEffectiveStatus(g)
    const matchStatus = !search.value.status || effectiveStatus === search.value.status
    return matchDest && matchDate && matchStatus
  })
})

const statusType = (s) => ({ '已开放': 'success', '已截止': 'info', '已满员': 'danger', '未开放': 'warning', '已出发': 'info', '已完成': '', '已取消': 'info' }[s] || 'info')

const disabledReason = (row) => {
  const s = getEffectiveStatus(row)
  if (s === '已满员') return '已满员'
  if (s === '已截止') return '已截止'
  if (s === '已出发') return '已出发'
  return s
}
</script>

<template>
  <el-card>
    <template #header><span>旅游团查询</span></template>

    <el-form :inline="true" style="margin-bottom: 16px">
      <el-form-item label="目的地">
        <el-input v-model="search.dest" placeholder="输入目的地" clearable />
      </el-form-item>
      <el-form-item label="出发日期">
        <el-date-picker v-model="search.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" clearable />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="search.status" placeholder="全部" clearable>
          <el-option label="已开放" value="已开放" />
          <el-option label="已截止" value="已截止" />
          <el-option label="已满员" value="已满员" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button @click="search = { dest: '', date: '', status: '' }">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="filtered" stripe>
      <el-table-column prop="group_code" label="旅游团代码" width="140" />
      <el-table-column prop="route_name" label="路线名称" />
      <el-table-column prop="departure_date" label="出发日期" width="110" />
      <el-table-column prop="deadline" label="截止日期" width="110" />
      <el-table-column prop="capacity" label="人数限额" width="90" />
      <el-table-column prop="current_count" label="已报名" width="80" />
      <el-table-column label="剩余名额" width="90">
        <template #default="{ row }">
          <b :style="{ color: row.capacity - row.current_count <= 5 ? '#fa8c16' : '#52c41a' }">
            {{ row.capacity - row.current_count }}
          </b>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(getEffectiveStatus(row))" size="small">
            {{ getEffectiveStatus(row) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90">
        <template #default="{ row }">
          <el-tooltip v-if="!canApply(row)" :content="disabledReason(row)" placement="top">
            <el-button size="small" disabled>{{ disabledReason(row) }}</el-button>
          </el-tooltip>
          <el-button v-else type="primary" size="small" @click="router.push(`/apply?group=${row.group_code}`)">申请</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
