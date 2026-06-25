import request from './request'

export const getFinanceExport = (params) => request.get('/api/finance/export', { params })
export const exportFinance = (data) => request.post('/api/finance/export', data)
export const getStats = () => request.get('/api/stats')
