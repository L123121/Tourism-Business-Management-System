import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '@/api/auth'

const ROLE_MENUS = {
  receptionist: ['home', 'query', 'apply', 'participant', 'change'],
  collector: ['home', 'query', 'balance', 'print'],
  routeAdmin: ['home', 'query', 'route', 'activity', 'price'],
  accountant: ['home', 'query', 'finance'],
  admin: ['home', 'query', 'apply', 'participant', 'balance', 'change', 'print', 'route', 'activity', 'price', 'finance'],
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => userInfo.value?.role || '')
  const menus = computed(() => userInfo.value?.menus || ROLE_MENUS[role.value] || [])
  const realName = computed(() => userInfo.value?.real_name || '')

  async function login(username, password) {
    const data = await loginApi({ username, password })
    token.value = data.token
    userInfo.value = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, userInfo, isLoggedIn, role, menus, realName, login, logout }
})
