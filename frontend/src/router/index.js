import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const PAGE_MENU_MAP = {
  '/home': 'home',
  '/tour-query': 'query',
  '/apply': 'apply',
  '/participant': 'participant',
  '/balance': 'balance',
  '/change': 'change',
  '/print': 'print',
  '/route': 'route',
  '/activity': 'activity',
  '/price': 'price',
  '/finance': 'finance',
}

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layout/AppLayout.vue'),
    redirect: '/home',
    children: [
      { path: 'home', name: 'Home', component: () => import('@/views/Home.vue'), meta: { title: '首页' } },
      { path: 'tour-query', name: 'TourQuery', component: () => import('@/views/TourQuery.vue'), meta: { title: '旅游团查询' } },
      { path: 'apply', name: 'ApplyCreate', component: () => import('@/views/ApplyCreate.vue'), meta: { title: '办理旅游申请' } },
      { path: 'apply/:applyNo', name: 'ApplyDetail', component: () => import('@/views/ApplyCreate.vue'), meta: { title: '办理旅游申请' } },
      { path: 'participant', name: 'ParticipantManage', component: () => import('@/views/ParticipantManage.vue'), meta: { title: '参加者信息管理' } },
      { path: 'participant/:applyNo', name: 'ParticipantDetail', component: () => import('@/views/ParticipantManage.vue'), meta: { title: '参加者信息管理' } },
      { path: 'balance', name: 'BalancePayment', component: () => import('@/views/BalancePayment.vue'), meta: { title: '余款支付管理' } },
      { path: 'change', name: 'ApplyChange', component: () => import('@/views/ApplyChange.vue'), meta: { title: '申请变更/取消' } },
      { path: 'print', name: 'PrintCenter', component: () => import('@/views/PrintCenter.vue'), meta: { title: '确认书/交款单打印' } },
      { path: 'route', name: 'RouteManage', component: () => import('@/views/RouteManage.vue'), meta: { title: '旅游路线管理' } },
      { path: 'activity', name: 'ActivityManage', component: () => import('@/views/ActivityManage.vue'), meta: { title: '旅游活动管理' } },
      { path: 'price', name: 'PriceSetting', component: () => import('@/views/PriceSetting.vue'), meta: { title: '价格设定' } },
      { path: 'finance', name: 'FinanceExport', component: () => import('@/views/FinanceExport.vue'), meta: { title: '财务数据导出' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.public) {
    next()
    return
  }

  if (!userStore.isLoggedIn) {
    next('/login')
    return
  }

  const pathBase = '/' + to.path.split('/').filter(Boolean)[0]
  const requiredMenu = PAGE_MENU_MAP[pathBase]
  if (requiredMenu && !userStore.menus.includes(requiredMenu)) {
    ElMessage.error('无权访问此页面')
    next('/home')
    return
  }

  next()
})

export default router
