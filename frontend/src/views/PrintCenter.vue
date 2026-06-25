<script setup>
import { ref, onMounted } from 'vue'
import { getApplications, getApplication } from '@/api/application'
import { ElMessage } from 'element-plus'

const applications = ref([])
const selected = ref([])
const printData = ref([])
const showDialog = ref(false)

onMounted(async () => {
  try { applications.value = await getApplications() } catch (e) { /* handled */ }
})

async function handlePrint(type) {
  if (selected.value.length === 0) { ElMessage.warning('请至少选择一条记录'); return }
  const details = []
  for (const app of selected.value) {
    try {
      const detail = await getApplication(app.apply_no)
      details.push(detail)
    } catch (e) { /* skip */ }
  }
  printData.value = details
  showDialog.value = true
}

function doPrint() {
  window.print()
  showDialog.value = false
}

function formatDate(d) {
  if (!d) return ''
  return d.replace(/-/g, '年').replace(/年(\d+)$/, '月$1日')
}
</script>

<template>
  <el-card>
    <template #header><span>确认书/余额交款单打印</span></template>

    <el-alert type="info" :closable="false" style="margin-bottom: 16px">
      每天负责催款的员工通过此功能打印前一天已完成申请的旅游确认书和余额交款单。
    </el-alert>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <div>
        <el-button @click="handlePrint('confirm')">批量打印确认书</el-button>
        <el-button type="primary" @click="handlePrint('receipt')">批量打印交款单</el-button>
      </div>
    </div>

    <el-table :data="applications" stripe @selection-change="(val) => selected = val">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="apply_no" label="申请编号" width="160" />
      <el-table-column prop="route_name" label="旅游团" />
      <el-table-column prop="departure_date" label="出发日期" width="110" />
      <el-table-column prop="responsible_name" label="申请责任人" width="100" />
      <el-table-column label="参加人数" width="100">
        <template #default="{ row }">{{ row.adult_count }}大{{ row.child_count }}小</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '已完成' ? 'success' : row.status === '进行中' ? 'primary' : 'info'" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default>
          <el-button type="primary" link size="small" @click="handlePrint('receipt')">打印</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 打印预览弹窗 -->
    <el-dialog v-model="showDialog" title="打印预览" width="800px" :before-close="() => showDialog = false">
      <div class="print-area">
        <div v-for="(app, idx) in printData" :key="app.apply_no" class="receipt-page">
          <div class="receipt-header">
            <h2>旅游业务管理系统</h2>
            <h3>余款交款单</h3>
          </div>
          <table class="receipt-table">
            <tr><td class="label">申请编号</td><td>{{ app.apply_no }}</td><td class="label">申请日期</td><td>{{ app.apply_date }}</td></tr>
            <tr><td class="label">旅游团</td><td>{{ app.route_name }}</td><td class="label">出发日期</td><td>{{ app.departure_date }}</td></tr>
            <tr><td class="label">申请责任人</td><td>{{ app.responsible_name }}</td><td class="label">联系电话</td><td>{{ app.responsible_phone }}</td></tr>
            <tr><td class="label">参加人数</td><td>{{ app.adult_count }}大{{ app.child_count }}小</td><td class="label">总费用</td><td>¥{{ app.total_fee?.toLocaleString() }}</td></tr>
            <tr><td class="label">已付订金</td><td>¥{{ app.deposit?.toLocaleString() }}</td><td class="label">待付余款</td><td style="color: #ff4d4f; font-weight: bold;">¥{{ (app.total_fee - app.deposit)?.toLocaleString() }}</td></tr>
          </table>
          <div class="receipt-participants">
            <h4>参加者名单</h4>
            <table class="participant-table">
              <thead><tr><th>姓名</th><th>性别</th><th>年龄</th><th>类型</th><th>联系电话</th></tr></thead>
              <tbody>
                <tr v-for="p in app.participants || []" :key="p.id">
                  <td>{{ p.name }}</td><td>{{ p.gender }}</td><td>{{ p.age }}</td><td>{{ p.type }}</td><td>{{ p.phone || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="receipt-footer">
            <div class="sign-row">
              <span>收费员签字：_______________</span>
              <span>日期：_______________</span>
            </div>
            <div class="sign-row">
              <span>申请人签字：_______________</span>
              <span>日期：_______________</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="doPrint">确认打印</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.receipt-page {
  page-break-after: always;
  padding: 20px;
  border: 1px solid #eee;
  margin-bottom: 20px;
  background: #fff;
}
.receipt-page:last-child { page-break-after: auto; }
.receipt-header { text-align: center; margin-bottom: 20px; }
.receipt-header h2 { font-size: 18px; margin-bottom: 4px; }
.receipt-header h3 { font-size: 14px; color: #666; }
.receipt-table { width: 100%; border-collapse: collapse; }
.receipt-table td { padding: 8px 12px; border: 1px solid #ddd; font-size: 13px; }
.receipt-table .label { background: #fafafa; color: #666; width: 100px; }
.receipt-participants { margin-top: 16px; }
.receipt-participants h4 { font-size: 13px; margin-bottom: 8px; }
.participant-table { width: 100%; border-collapse: collapse; }
.participant-table th, .participant-table td { padding: 6px 10px; border: 1px solid #ddd; font-size: 12px; text-align: center; }
.participant-table th { background: #fafafa; }
.receipt-footer { margin-top: 30px; }
.sign-row { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13px; }
</style>

<style>
@media print {
  body * { visibility: hidden; }
  .print-area, .print-area * { visibility: visible; }
  .print-area { position: absolute; left: 0; top: 0; width: 100%; padding: 20px; }
  .receipt-page { border: none; box-shadow: none; }
}
</style>
