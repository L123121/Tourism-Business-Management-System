<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const menuConfig = [
  {
    group: '业务办理',
    items: [
      { page: 'home', label: '首页', icon: 'HomeFilled', path: '/home' },
      { page: 'query', label: '旅游团查询', icon: 'Search', path: '/tour-query' },
      { page: 'apply', label: '办理旅游申请', icon: 'Edit', path: '/apply' },
      { page: 'participant', label: '参加者信息管理', icon: 'User', path: '/participant' },
      { page: 'balance', label: '余款支付管理', icon: 'Money', path: '/balance' },
      { page: 'change', label: '申请变更/取消', icon: 'Switch', path: '/change' },
    ],
  },
  {
    group: '打印中心',
    pages: ['print'],
    items: [
      { page: 'print', label: '确认书/交款单打印', icon: 'Printer', path: '/print' },
    ],
  },
  {
    group: '后台管理',
    pages: ['route', 'activity', 'price'],
    items: [
      { page: 'route', label: '旅游路线管理', icon: 'MapLocation', path: '/route' },
      { page: 'activity', label: '旅游活动管理', icon: 'Flag', path: '/activity' },
      { page: 'price', label: '价格设定', icon: 'PriceTag', path: '/price' },
    ],
  },
  {
    group: '财务',
    pages: ['finance'],
    items: [
      { page: 'finance', label: '财务数据导出', icon: 'DataAnalysis', path: '/finance' },
    ],
  },
]

const visibleMenus = computed(() => {
  const menus = userStore.menus
  return menuConfig
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => menus.includes(item.page)),
    }))
    .filter((group) => group.items.length > 0)
})

function navigate(path) {
  router.push(path)
}
</script>

<template>
  <div class="app-sidebar">
    <template v-for="group in visibleMenus" :key="group.group">
      <div class="menu-group">{{ group.group }}</div>
      <div
        v-for="item in group.items"
        :key="item.page"
        class="menu-item"
        :class="{ active: route.path === item.path }"
        @click="navigate(item.path)"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.app-sidebar {
  height: 100%;
  overflow-y: auto;
  padding-top: 8px;
}
.menu-group {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  padding: 16px 16px 6px;
  letter-spacing: 1px;
}
.menu-item {
  color: rgba(255, 255, 255, 0.65);
  padding: 11px 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  border-left: 3px solid transparent;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}
.menu-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.06);
}
.menu-item.active {
  color: #fff;
  background: #1890ff;
  border-left-color: #fff;
}
</style>
