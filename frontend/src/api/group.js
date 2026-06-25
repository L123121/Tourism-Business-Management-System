import request from './request'

export const getGroups = (params) => request.get('/api/groups', { params })
export const getGroup = (code) => request.get(`/api/groups/${code}`)
export const createGroup = (data) => request.post('/api/groups', data)
