<script setup>
import { ref, onMounted } from 'vue'
import { getFinanceExport, exportFinance, getStats } from '@/api/finance'
import { ElMessage, ElMessageBox } from 'element-plus'

const records = ref([])
const search = ref({ start: '', end: '', type: '' })
const stats = ref({ monthly_applications: 0, today_applications: 0, pending_balance: 0, upcoming_groups: 0 })

onMounted(async () => {
  try {
    const [s, r] = await Promise.all([getStats(), getFinanceExport()])
    stats.value = s
    records.value = r
  } catch (e) { /* handled */ }
})

async function handleSearch() {
  try { records.value = await getFinanceExport(search.value) } catch (e) { /* handled */ }
}

async function handleExport() {
  try {
    await ElMessageBox.confirm('确认将查询范围内的交易数据导出到财务系统？', '确认导出', { type: 'info' })
    const result = await exportFinance(search.value)
    ElMessage.success(result.message || '导出成功')
    records.value = await getFinanceExport(search.value)
  } catch (e) { /* handled */ }
}

const payType = (t) => ({ '订金': 'primary', '余款': 'warning', '退款': 'danger' }[t] || 'info')
</script>

<template>
  <el-card>
    <template #header><span>财务数据导出</span></template>

    <el-alert type="info" :closable="false" style="margin-bottom: 16px">
      每天晚上系统会自动将当天与现金相关的订金、支付信息全部导出到财务系统。
    </el-alert>

    <el-form :inline="true" style="margin-bottom: 16px">
      <el-form-item label="日期范围">
        <el-date-picker v-model="search.start" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" />
        <span style="margin: 0 8px">至</span>
        <el-date-picker v-model="search.end" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" />
      </el-form-item>
      <el-form-item label="交易类型">
        <el-select v-model="search.type" placeholder="全部" clearable>
          <el-option label="订金" value="订金" />
          <el-option label="余款" value="余款" />
          <el-option label="退款" value="退款" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button type="success" @click="handleExport">导出到财务系统</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="records" stripe>
      <el-table-column prop="payment_no" label="交易编号" width="160" />
      <el-table-column prop="pay_date" label="日期" width="110" />
      <el-table-column prop="apply_no" label="申请编号" width="160" />
      <el-table-column prop="route_name" label="旅游团" />
      <el-table-column prop="responsible_name" label="申请人" width="80" />
      <el-table-column label="交易类型" width="80">
        <template #default="{ row }">
          <el-tag :type="payType(row.pay_type)" size="small">{{ row.pay_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="金额" width="100">
        <template #default="{ row }">
          <span :style="{ color: row.amount >= 0 ? '#52c41a' : '#ff4d4f' }">
            {{ row.amount >= 0 ? '+' : '' }}¥{{ row.amount?.toLocaleString() }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="pay_method" label="支付方式" width="90" />
      <el-table-column label="导出状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.exported ? 'success' : 'info'" size="small">{{ row.exported ? '已导出' : '未导出' }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
