<script setup>
import { ref, onMounted } from 'vue'
import { getPendingBalance, payBalance } from '@/api/balance'
import { ElMessage } from 'element-plus'

const pendingList = ref([])
const searchNo = ref('')
const selectedApp = ref(null)
const payForm = ref({ amount: 0, pay_method: '现金' })
const loading = ref(false)

onMounted(async () => {
  try { pendingList.value = await getPendingBalance() } catch (e) { /* handled */ }
})

function selectApp(app) {
  selectedApp.value = app
  const paid = app.paid_total || 0
  payForm.value.amount = (app.total_fee || 0) - paid
}

async function handlePay() {
  if (!selectedApp.value || payForm.value.amount <= 0) { ElMessage.warning('请输入有效金额'); return }
  loading.value = true
  try {
    await payBalance(selectedApp.value.apply_no, payForm.value)
    ElMessage.success('余款支付成功')
    selectedApp.value = null
    pendingList.value = await getPendingBalance()
  } catch (e) { /* handled */ } finally { loading.value = false }
}
</script>

<template>
  <el-card>
    <template #header><span>余款支付管理</span></template>

    <el-table :data="pendingList" stripe highlight-current-row @current-change="selectApp">
      <el-table-column prop="apply_no" label="申请编号" width="160" />
      <el-table-column prop="route_name" label="旅游团" />
      <el-table-column prop="departure_date" label="出发日期" width="110" />
      <el-table-column prop="responsible_name" label="申请责任人" width="100" />
      <el-table-column label="总费用" width="100">
        <template #default="{ row }">¥{{ row.total_fee?.toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="已付订金" width="100">
        <template #default="{ row }">¥{{ row.paid_total?.toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="待付余款" width="100">
        <template #default="{ row }">
          <span style="color: #ff4d4f; font-weight: 600">¥{{ ((row.total_fee || 0) - (row.paid_total || 0)).toLocaleString() }}</span>
        </template>
      </el-table-column>
    </el-table>

    <el-card v-if="selectedApp" style="margin-top: 16px" shadow="never">
      <template #header><span>录入余款支付信息</span></template>
      <el-descriptions :column="3" border style="margin-bottom: 16px">
        <el-descriptions-item label="申请编号">{{ selectedApp.apply_no }}</el-descriptions-item>
        <el-descriptions-item label="旅游团">{{ selectedApp.route_name }}</el-descriptions-item>
        <el-descriptions-item label="待付余款" label-style="color: #ff4d4f">
          ¥{{ ((selectedApp.total_fee || 0) - (selectedApp.paid_total || 0)).toLocaleString() }}
        </el-descriptions-item>
      </el-descriptions>
      <el-form :inline="true">
        <el-form-item label="支付金额">
          <el-input-number v-model="payForm.amount" :min="1" />
        </el-form-item>
        <el-form-item label="支付方式">
          <el-select v-model="payForm.pay_method">
            <el-option label="现金" value="现金" />
            <el-option label="银行转账" value="银行转账" />
            <el-option label="微信支付" value="微信支付" />
            <el-option label="支付宝" value="支付宝" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="success" :loading="loading" @click="handlePay">确认收款</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </el-card>
</template>
