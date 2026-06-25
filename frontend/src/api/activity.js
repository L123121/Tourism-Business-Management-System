import request from './request'

export const getActivities = (params) => request.get('/api/activities', { params })
export const createActivity = (data) => request.post('/api/activities', data)
export const updateActivity = (code, data) => request.put(`/api/activities/${code}`, data)
