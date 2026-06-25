import request from './request'

export const getPrices = () => request.get('/api/prices')
export const getPrice = (groupCode) => request.get(`/api/prices/${groupCode}`)
export const updatePrice = (groupCode, data) => request.put(`/api/prices/${groupCode}`, data)
export const publishPrice = (groupCode) => request.post(`/api/prices/${groupCode}/publish`)
