import request from './request'

export const getRoutes = () => request.get('/api/routes')
export const getRoute = (code) => request.get(`/api/routes/${code}`)
export const createRoute = (data) => request.post('/api/routes', data)
export const updateRoute = (code, data) => request.put(`/api/routes/${code}`, data)
export const cancelRoute = (code, data) => request.post(`/api/routes/${code}/cancel`, data)
