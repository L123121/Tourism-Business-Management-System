<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const form = ref({ username: '', password: '' })
const loading = ref(false)

// 已登录则跳转
onMounted(() => {
  if (userStore.isLoggedIn) router.replace('/')
})

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

function quickLogin(username) {
  form.value.username = username
  form.value.password = 'Travel@2026'
  handleLogin()
}

const accounts = [
  { username: 'zhangmin', name: '张敏', role: '前台员工', color: '#13c2c2' },
  { username: 'lihua', name: '李华', role: '催款员工', color: '#fa8c16' },
  { username: 'wanglei', name: '王磊', role: '路线管理员', color: '#2f54eb' },
  { username: 'zhaofang', name: '赵芳', role: '会计人员', color: '#eb2f96' },
]
</script>

<template>
  <div class="login-page">
    <div class="particles"></div>
    <div class="login-card">
      <div class="logo">
        <div class="logo-icon">
          <el-icon :size="36" color="#fff"><Location /></el-icon>
        </div>
        <h1>旅游业务管理系统</h1>
        <p>Travel Business Management System</p>
      </div>

      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          style="width: 100%; border-radius: 12px; font-size: 15px; letter-spacing: 2px"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>

      <div class="test-accounts">
        <h4>快速登录 · 点击选择账号</h4>
        <div class="account-grid">
          <div
            v-for="acc in accounts"
            :key="acc.username"
            class="account-chip"
            @click="quickLogin(acc.username)"
          >
            <div class="chip-avatar" :style="{ background: acc.color }">
              {{ acc.name[0] }}
            </div>
            <div>
              <div class="chip-name">{{ acc.name }}</div>
              <div class="chip-role">{{ acc.role }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="footer">© 2026 旅游业务管理系统 · 课程设计项目</div>
  </div>
</template>

<script>
import { User, Lock } from '@element-plus/icons-vue'
export default { components: { User, Lock } }
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}
.login-page::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 50%;
  top: -200px;
  right: -100px;
}
.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 48px 40px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  animation: cardIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(30px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.logo {
  text-align: center;
  margin-bottom: 36px;
}
.logo-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35);
}
.logo h1 {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a2e;
}
.logo p {
  font-size: 13px;
  color: #999;
  margin-top: 6px;
}
.test-accounts {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}
.test-accounts h4 {
  font-size: 12px;
  color: #bbb;
  font-weight: 400;
  margin-bottom: 12px;
  text-align: center;
}
.account-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.account-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f8f9fa;
  border: 1px solid #eee;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
}
.account-chip:hover {
  background: #eef2ff;
  border-color: #667eea;
  transform: translateY(-1px);
}
.chip-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #fff;
  font-weight: 600;
  flex-shrink: 0;
}
.chip-name {
  font-weight: 600;
  color: #333;
}
.chip-role {
  color: #999;
  font-size: 11px;
}
.footer {
  position: absolute;
  bottom: 20px;
  text-align: center;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}
</style>
