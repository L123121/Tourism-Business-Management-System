import request from './request'

export const getApplications = () => request.get('/api/applications')
export const getApplication = (applyNo) => request.get(`/api/applications/${applyNo}`)
export const createApplication = (data) => request.post('/api/applications', data)
export const cancelApplication = (applyNo, data) => request.post(`/api/applications/${applyNo}/cancel`, data)
export const calcDeposit = (data) => request.post('/api/calc-deposit', data)
export const calcCancelFee = (data) => request.post('/api/calc-cancel-fee', data)
