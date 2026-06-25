import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('element-plus', () => ({
  ElMessage: { error: vi.fn(), success: vi.fn() },
}))

import router from '@/router'
import { useUserStore } from '@/stores/user'

describe('路由配置', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('定义了登录路由', () => {
    const loginRoute = router.getRoutes().find(r => r.path === '/login')
    expect(loginRoute).toBeDefined()
    expect(loginRoute.meta.public).toBe(true)
  })

  it('定义了首页路由', () => {
    const homeRoute = router.getRoutes().find(r => r.path === '/home')
    expect(homeRoute).toBeDefined()
  })

  it('定义了旅游团查询路由', () => {
    const route = router.getRoutes().find(r => r.path === '/tour-query')
    expect(route).toBeDefined()
  })

  it('定义了办理申请路由', () => {
    const route = router.getRoutes().find(r => r.path === '/apply')
    expect(route).toBeDefined()
  })

  it('定义了参加者管理路由', () => {
    const route = router.getRoutes().find(r => r.path === '/participant')
    expect(route).toBeDefined()
  })

  it('定义了余款支付路由', () => {
    const route = router.getRoutes().find(r => r.path === '/balance')
    expect(route).toBeDefined()
  })

  it('定义了路线管理路由', () => {
    const route = router.getRoutes().find(r => r.path === '/route')
    expect(route).toBeDefined()
  })

  it('定义了活动管理路由', () => {
    const route = router.getRoutes().find(r => r.path === '/activity')
    expect(route).toBeDefined()
  })

  it('定义了价格设定路由', () => {
    const route = router.getRoutes().find(r => r.path === '/price')
    expect(route).toBeDefined()
  })

  it('定义了财务导出路由', () => {
    const route = router.getRoutes().find(r => r.path === '/finance')
    expect(route).toBeDefined()
  })

  it('根路径重定向到 /home', () => {
    const rootRoute = router.getRoutes().find(r => r.path === '/')
    expect(rootRoute).toBeDefined()
    expect(rootRoute.redirect).toBe('/home')
  })

  it('定义了申请详情路由（带参数）', () => {
    const route = router.getRoutes().find(r => r.path === '/apply/:applyNo')
    expect(route).toBeDefined()
  })
})

describe('路由守卫 — 权限控制', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('未登录时访问受保护页面应跳转到 /login', async () => {
    const store = useUserStore()
    expect(store.isLoggedIn).toBe(false)

    await router.push('/home')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('已登录时可以访问 /home', async () => {
    const store = useUserStore()
    store.token = 'test-token'
    store.userInfo = {
      id: 1, username: 'admin', role: 'admin', real_name: '管理员',
      menus: ['home', 'query', 'apply', 'participant', 'balance', 'change', 'print', 'route', 'activity', 'price', 'finance'],
    }

    await router.push('/home')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/home')
  })

  it('登录页面不需要认证', async () => {
    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('前台员工不能访问财务页面', async () => {
    const store = useUserStore()
    store.token = 'test-token'
    store.userInfo = {
      id: 1, username: 'zhangmin', role: 'receptionist',
      menus: ['home', 'query', 'apply', 'participant', 'change'],
    }

    await router.push('/finance')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/home')
  })

  it('会计人员不能访问路线管理页面', async () => {
    const store = useUserStore()
    store.token = 'test-token'
    store.userInfo = {
      id: 4, username: 'zhaofang', role: 'accountant',
      menus: ['home', 'query', 'finance'],
    }

    await router.push('/route')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/home')
  })

  it('管理员可以访问所有页面', async () => {
    const store = useUserStore()
    store.token = 'test-token'
    store.userInfo = {
      id: 5, username: 'admin', role: 'admin',
      menus: ['home', 'query', 'apply', 'participant', 'balance', 'change', 'print', 'route', 'activity', 'price', 'finance'],
    }

    const pages = ['/home', '/route', '/finance', '/price', '/balance']
    for (const page of pages) {
      await router.push(page)
      await router.isReady()
      expect(router.currentRoute.value.path).toBe(page)
    }
  })
})
