<script setup>
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const ROLE_NAMES = {
  receptionist: '前台员工',
  collector: '催款员工',
  routeAdmin: '路线管理员',
  accountant: '会计人员',
  admin: '系统管理员',
}

function doLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-header">
    <h1>旅游业务管理系统</h1>
    <div class="user-info">
      <span>
        欢迎，<b>{{ userStore.realName }}</b>
        （{{ ROLE_NAMES[userStore.role] || userStore.role }}）
      </span>
      <span class="date">{{ new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }) }}</span>
      <a class="logout" @click="doLogout">退出登录</a>
    </div>
  </div>
</template>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  padding: 0 24px;
  height: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
.app-header h1 {
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 1px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}
.date {
  opacity: 0.7;
}
.logout {
  color: #ffd591;
  cursor: pointer;
  text-decoration: none;
}
.logout:hover {
  text-decoration: underline;
}
</style>
