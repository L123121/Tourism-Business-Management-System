import axios from 'axios'
import { useUserStore } from '@/stores/user'
import router from '@/router'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/',
  timeout: 10000,
})

// 请求拦截器：自动注入 token
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data, config } = error.response
      if (status === 401) {
        const userStore = useUserStore()
        userStore.logout()
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else if (!config?.suppressError) {
        ElMessage.error(data?.error || '请求失败')
      }
    } else if (!error.config?.suppressError) {
      ElMessage.error('网络错误，请检查后端是否启动')
    }
    return Promise.reject(error)
  }
)

export default request
