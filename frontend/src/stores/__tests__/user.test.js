import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
}))

import { useUserStore } from '@/stores/user'
import { login as loginApi } from '@/api/auth'

describe('useUserStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('未登录时 isLoggedIn 为 false', () => {
      const store = useUserStore()
      expect(store.isLoggedIn).toBe(false)
    })

    it('role 为空字符串', () => {
      const store = useUserStore()
      expect(store.role).toBe('')
    })

    it('menus 为空数组', () => {
      const store = useUserStore()
      expect(store.menus).toEqual([])
    })
  })

  describe('login', () => {
    it('登录成功后保存 token 和 userInfo', async () => {
      loginApi.mockResolvedValue({
        token: 'test-token-abc',
        user: { id: 1, username: 'admin', role: 'admin', real_name: '管理员', menus: ['home', 'query'] },
      })

      const store = useUserStore()
      await store.login('admin', '123456')

      expect(store.token).toBe('test-token-abc')
      expect(store.isLoggedIn).toBe(true)
      expect(store.role).toBe('admin')
      expect(store.realName).toBe('管理员')
      expect(store.menus).toEqual(['home', 'query'])
    })

    it('登录后数据持久化到 localStorage', async () => {
      loginApi.mockResolvedValue({
        token: 'saved-token',
        user: { id: 2, username: 'zhangmin', role: 'receptionist', real_name: '张敏' },
      })

      const store = useUserStore()
      await store.login('zhangmin', '123456')

      expect(localStorage.getItem('token')).toBe('saved-token')
      const savedUser = JSON.parse(localStorage.getItem('user'))
      expect(savedUser.username).toBe('zhangmin')
    })

    it('登录失败时 store 状态不变', async () => {
      loginApi.mockRejectedValue(new Error('用户名或密码错误'))

      const store = useUserStore()
      await expect(store.login('admin', 'wrong')).rejects.toThrow()

      expect(store.token).toBe('')
      expect(store.isLoggedIn).toBe(false)
    })
  })

  describe('logout', () => {
    it('退出后清空 token 和 userInfo', async () => {
      loginApi.mockResolvedValue({
        token: 'to-be-cleared',
        user: { id: 1, username: 'admin', role: 'admin' },
      })

      const store = useUserStore()
      await store.login('admin', '123456')
      expect(store.isLoggedIn).toBe(true)

      store.logout()
      expect(store.token).toBe('')
      expect(store.userInfo).toBeNull()
      expect(store.isLoggedIn).toBe(false)
      expect(localStorage.getItem('token')).toBeNull()
    })
  })

  describe('角色菜单映射', () => {
    it('前台员工拥有正确菜单', async () => {
      loginApi.mockResolvedValue({
        token: 't',
        user: { id: 1, role: 'receptionist', menus: ['home', 'query', 'apply', 'participant', 'change'] },
      })

      const store = useUserStore()
      await store.login('zhangmin', '123456')

      expect(store.menus).toContain('apply')
      expect(store.menus).toContain('participant')
      expect(store.menus).not.toContain('finance')
      expect(store.menus).not.toContain('price')
    })

    it('催款员工拥有正确菜单', async () => {
      loginApi.mockResolvedValue({
        token: 't',
        user: { id: 2, role: 'collector', menus: ['home', 'query', 'balance', 'print'] },
      })

      const store = useUserStore()
      await store.login('lihua', '123456')

      expect(store.menus).toContain('balance')
      expect(store.menus).toContain('print')
      expect(store.menus).not.toContain('apply')
      expect(store.menus).not.toContain('finance')
    })

    it('管理员拥有全部菜单', async () => {
      loginApi.mockResolvedValue({
        token: 't',
        user: { id: 5, role: 'admin', menus: ['home', 'query', 'apply', 'participant', 'balance', 'change', 'print', 'route', 'activity', 'price', 'finance'] },
      })

      const store = useUserStore()
      await store.login('admin', '123456')

      expect(store.menus).toContain('apply')
      expect(store.menus).toContain('finance')
      expect(store.menus).toContain('price')
      expect(store.menus).toContain('route')
    })
  })

  describe('从 localStorage 恢复', () => {
    it('页面刷新后从 localStorage 恢复登录状态', () => {
      localStorage.setItem('token', 'restored-token')
      localStorage.setItem('user', JSON.stringify({
        id: 1, username: 'admin', role: 'admin', real_name: '管理员',
        menus: ['home', 'finance'],
      }))

      const store = useUserStore()
      expect(store.isLoggedIn).toBe(true)
      expect(store.token).toBe('restored-token')
      expect(store.role).toBe('admin')
      expect(store.realName).toBe('管理员')
    })
  })
})
