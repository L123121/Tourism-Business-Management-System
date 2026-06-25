import request from './request'

export const login = (data) => request.post('/api/login', data)
export const register = (data) => request.post('/api/register', data)
export const getUserInfo = () => request.get('/api/user/info')
export const changePassword = (data) => request.put('/api/user/password', data)
export const getUsers = () => request.get('/api/users')
