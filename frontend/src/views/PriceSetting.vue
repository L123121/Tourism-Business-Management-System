<script setup>
import { ref, onMounted } from 'vue'
import { getPrices, getPrice, updatePrice, publishPrice } from '@/api/price'
import { getGroups } from '@/api/group'
import { ElMessage, ElMessageBox } from 'element-plus'

const prices = ref([])
const groups = ref([])
const groupCode = ref('')
const priceForm = ref({ adult_price: 0, child_price: 0, discount: '' })
const isPublished = ref(false)
const loading = ref(false)

onMounted(async () => {
  try {
    const [p, g] = await Promise.all([getPrices(), getGroups()])
    prices.value = p
    groups.value = g
  } catch (e) { /* handled */ }
})

async function loadPrice() {
  if (!groupCode.value) return
  try {
    const p = await getPrice(groupCode.value)
    priceForm.value = { adult_price: p.adult_price, child_price: p.child_price, discount: p.discount || '' }
    isPublished.value = !!p.is_published
  } catch (e) {
    priceForm.value = { adult_price: 0, child_price: 0, discount: '' }
    isPublished.value = false
  }
}

async function handleSave() {
  loading.value = true
  try {
    await updatePrice(groupCode.value, priceForm.value)
    ElMessage.success('价格已保存')
    prices.value = await getPrices()
  } catch (e) { /* handled */ } finally { loading.value = false }
}

async function handlePublish() {
  try {
    await ElMessageBox.confirm('价格公开后将不可修改，确认公开？', '确认公开', { type: 'warning' })
    await publishPrice(groupCode.value)
    ElMessage.success('价格已公开')
    isPublished.value = true
    prices.value = await getPrices()
  } catch (e) { /* handled */ }
}
</script>

<template>
  <el-card style="margin-bottom: 16px">
    <template #header><span>价格设定</span></template>

    <el-form :inline="true" style="margin-bottom: 16px">
      <el-form-item label="旅游团代码">
        <el-select v-model="groupCode" filterable placeholder="选择旅游团代码" style="width: 240px" @change="loadPrice">
          <el-option v-for="g in groups" :key="g.group_code" :label="`${g.group_code} - ${g.activity_name || ''}`" :value="g.group_code" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadPrice">查询</el-button>
      </el-form-item>
    </el-form>

    <el-form label-width="120px">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="大人价格（元/人）">
            <el-input-number v-model="priceForm.adult_price" :min="0" :disabled="isPublished" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="小孩价格（元/人）">
            <el-input-number v-model="priceForm.child_price" :min="0" :disabled="isPublished" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="优惠措施">
            <el-input v-model="priceForm.discount" :disabled="isPublished" placeholder="输入优惠措施" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-alert v-if="isPublished" type="warning" :closable="false" style="margin-bottom: 16px">
        价格已公开，不可再修改。
      </el-alert>
      <el-form-item>
        <el-button v-if="!isPublished" @click="handleSave" :loading="loading">保存草稿</el-button>
        <el-button v-if="!isPublished" type="success" @click="handlePublish">公开价格</el-button>
      </el-form-item>
    </el-form>
  </el-card>

  <el-card>
    <template #header><span>价格总览</span></template>
    <el-table :data="prices" stripe>
      <el-table-column prop="group_code" label="旅游团代码" width="140" />
      <el-table-column prop="route_name" label="路线名称" />
      <el-table-column prop="departure_date" label="出发日期" width="110" />
      <el-table-column label="大人价格" width="100">
        <template #default="{ row }">¥{{ row.adult_price?.toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="小孩价格" width="100">
        <template #default="{ row }">¥{{ row.child_price?.toLocaleString() }}</template>
      </el-table-column>
      <el-table-column prop="discount" label="优惠措施" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
            {{ row.is_published ? '已公开' : '草稿' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
