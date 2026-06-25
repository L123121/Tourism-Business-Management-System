<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getGroups, getGroup } from '@/api/group'
import { createApplication, calcDeposit } from '@/api/application'
import { ElMessage } from 'element-plus'

const route = useRoute()
const groupCode = ref(route.query.group || '')
const groupInfo = ref(null)
const groupList = ref([])
const allGroups = ref([])
const groupLoading = ref(false)
const form = ref({ responsible_name: '', responsible_phone: '', responsible_idcard: '', gender: '男', age: null, adult_count: 1, child_count: 0, total_fee: 0 })
const depositInfo = ref(null)
const result = ref(null)
const loading = ref(false)

// 加载旅游团列表
async function loadGroups() {
  groupLoading.value = true
  try {
    const data = await getGroups({ status: '已开放' })
    const today = new Date().toISOString().split('T')[0]
    allGroups.value = data
      .filter(g => g.deadline >= today)  // 过滤掉已截止的旅游团
      .map(g => ({
        value: g.group_code,
        label: `${g.group_code} - ${g.route_name} (出发:${g.departure_date} 截止:${g.deadline})`,
        route_name: g.route_name,
        departure_date: g.departure_date,
        activity_name: g.activity_name,
        deadline: g.deadline,
      }))
    groupList.value = [...allGroups.value]
  } catch (e) {
    ElMessage.error('加载旅游团列表失败')
  } finally {
    groupLoading.value = false
  }
}

// 远程搜索过滤
function remoteMethod(query) {
  if (query) {
    groupLoading.value = true
    setTimeout(() => {
      groupLoading.value = false
      groupList.value = allGroups.value.filter(item =>
        item.value.toLowerCase().includes(query.toLowerCase()) ||
        item.label.toLowerCase().includes(query.toLowerCase())
      )
    }, 200)
  } else {
    groupList.value = [...allGroups.value]
  }
}

watch(groupCode, async (code) => {
  if (!code) {
    groupInfo.value = null
    depositInfo.value = null
    return
  }
  try {
    groupInfo.value = await getGroup(code)
    await calc()
  } catch (e) { groupInfo.value = null }
})

async function calc() {
  if (!groupInfo.value) return
  try {
    depositInfo.value = await calcDeposit({
      departure_date: groupInfo.value.departure_date,
      adult_count: form.value.adult_count,
      child_count: form.value.child_count,
    })
  } catch (e) { /* handled */ }
}

onMounted(() => {
  loadGroups()
  if (groupCode.value) calc()
})

async function handleSubmit() {
  if (!form.value.responsible_name || !form.value.responsible_phone) {
    ElMessage.warning('请填写申请责任人姓名和电话')
    return
  }
  if (!form.value.age || form.value.age < 1) {
    ElMessage.warning('请填写负责人年龄')
    return
  }
  loading.value = true
  try {
    const data = await createApplication({
      group_code: groupCode.value,
      ...form.value,
    })
    result.value = data
    ElMessage.success('申请办理成功')
  } catch (e) { /* handled */ } finally { loading.value = false }
}
</script>

<template>
  <div>
    <el-card v-if="!result">
      <template #header><span>办理旅游申请</span></template>

      <el-form label-width="100px">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="旅游团代码">
              <el-select
                v-model="groupCode"
                filterable
                remote
                :remote-method="remoteMethod"
                :loading="groupLoading"
                placeholder="请选择或搜索旅游团"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="item in groupList"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="路线名称">
              <el-input :model-value="groupInfo?.route_name || ''" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="出发日期">
              <el-input :model-value="groupInfo?.departure_date || ''" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider>申请责任人信息</el-divider>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="姓名"><el-input v-model="form.responsible_name" placeholder="请输入姓名" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="电话"><el-input v-model="form.responsible_phone" placeholder="请输入电话" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="身份证号"><el-input v-model="form.responsible_idcard" placeholder="请输入身份证号" /></el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="性别">
              <el-select v-model="form.gender" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="年龄"><el-input-number v-model="form.age" :min="1" :max="120" placeholder="请输入年龄" style="width: 100%" /></el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="大人人数">
              <el-input-number v-model="form.adult_count" :min="1" @change="calc" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="小孩人数">
              <el-input-number v-model="form.child_count" :min="0" @change="calc" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="总人数">
              <el-input :model-value="`${form.adult_count + form.child_count} 人`" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="总费用">
              <el-input-number v-model="form.total_fee" :min="0" :step="100" :precision="2" style="width: 100%" placeholder="请输入总费用" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider>订金计算</el-divider>

        <el-descriptions v-if="depositInfo" :column="2" border style="margin-bottom: 16px">
          <el-descriptions-item label="距出发天数">{{ depositInfo.days }} 天</el-descriptions-item>
          <el-descriptions-item label="订金标准">{{ depositInfo.per_person }} 元/人</el-descriptions-item>
          <el-descriptions-item label="大人人数">{{ form.adult_count }} 人</el-descriptions-item>
          <el-descriptions-item label="小孩人数">{{ form.child_count }} 人</el-descriptions-item>
        </el-descriptions>

        <div v-if="depositInfo" style="text-align: center; padding: 20px; background: #fff7e6; border-radius: 8px; margin-bottom: 16px">
          <div style="font-size: 13px; color: #999">应收取订金</div>
          <div style="font-size: 36px; font-weight: 700; color: #fa8c16">¥{{ depositInfo.total?.toLocaleString() }}</div>
        </div>

        <div style="text-align: right">
          <el-button type="success" :loading="loading" @click="handleSubmit">确认办理并收取订金</el-button>
        </div>
      </el-form>
    </el-card>

    <el-card v-else>
      <el-result icon="success" title="申请办理成功" :sub-title="`申请编号：${result.apply_no}`">
        <template #extra>
          <el-button type="primary" @click="result = null; groupCode = ''; groupInfo = null">继续办理</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>
