import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/stores/user', () => ({
  useUserStore: vi.fn(() => ({ token: 'mock-token' })),
}))

vi.mock('@/router', () => ({
  default: { push: vi.fn() },
}))

vi.mock('element-plus', () => ({
  ElMessage: { error: vi.fn(), success: vi.fn() },
}))

import request from '@/api/request'

describe('request 拦截器', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('request 实例已创建', () => {
    expect(request).toBeDefined()
    expect(request.interceptors).toBeDefined()
  })

  it('有请求拦截器', () => {
    expect(request.interceptors.request.handlers.length).toBeGreaterThan(0)
  })

  it('有响应拦截器', () => {
    expect(request.interceptors.response.handlers.length).toBeGreaterThan(0)
  })
})

describe('API 模块导出', () => {
  it('auth 模块导出所有函数', async () => {
    const auth = await import('@/api/auth')
    expect(typeof auth.login).toBe('function')
    expect(typeof auth.register).toBe('function')
    expect(typeof auth.getUserInfo).toBe('function')
    expect(typeof auth.changePassword).toBe('function')
    expect(typeof auth.getUsers).toBe('function')
  })

  it('application 模块导出所有函数', async () => {
    const app = await import('@/api/application')
    expect(typeof app.getApplications).toBe('function')
    expect(typeof app.getApplication).toBe('function')
    expect(typeof app.createApplication).toBe('function')
    expect(typeof app.cancelApplication).toBe('function')
    expect(typeof app.calcDeposit).toBe('function')
    expect(typeof app.calcCancelFee).toBe('function')
  })

  it('balance 模块导出所有函数', async () => {
    const balance = await import('@/api/balance')
    expect(typeof balance.getPendingBalance).toBe('function')
    expect(typeof balance.payBalance).toBe('function')
  })

  it('route 模块导出所有函数', async () => {
    const route = await import('@/api/route')
    expect(typeof route.getRoutes).toBe('function')
    expect(typeof route.getRoute).toBe('function')
    expect(typeof route.createRoute).toBe('function')
    expect(typeof route.updateRoute).toBe('function')
    expect(typeof route.cancelRoute).toBe('function')
  })

  it('group 模块导出所有函数', async () => {
    const group = await import('@/api/group')
    expect(typeof group.getGroups).toBe('function')
    expect(typeof group.getGroup).toBe('function')
    expect(typeof group.createGroup).toBe('function')
  })

  it('participant 模块导出所有函数', async () => {
    const participant = await import('@/api/participant')
    expect(typeof participant.getParticipants).toBe('function')
    expect(typeof participant.addParticipant).toBe('function')
    expect(typeof participant.updateParticipant).toBe('function')
    expect(typeof participant.cancelParticipant).toBe('function')
    expect(typeof participant.changeResponsible).toBe('function')
  })

  it('price 模块导出所有函数', async () => {
    const price = await import('@/api/price')
    expect(typeof price.getPrices).toBe('function')
    expect(typeof price.getPrice).toBe('function')
    expect(typeof price.updatePrice).toBe('function')
    expect(typeof price.publishPrice).toBe('function')
  })

  it('activity 模块导出所有函数', async () => {
    const activity = await import('@/api/activity')
    expect(typeof activity.getActivities).toBe('function')
    expect(typeof activity.createActivity).toBe('function')
    expect(typeof activity.updateActivity).toBe('function')
  })

  it('finance 模块导出所有函数', async () => {
    const finance = await import('@/api/finance')
    expect(typeof finance.getFinanceExport).toBe('function')
    expect(typeof finance.exportFinance).toBe('function')
    expect(typeof finance.getStats).toBe('function')
  })
})
