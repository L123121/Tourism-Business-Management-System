import request from './request'

export const getPendingBalance = () => request.get('/api/balance/pending')
export const payBalance = (applyNo, data) => request.post(`/api/applications/${applyNo}/pay-balance`, data)
