import request from './request'

export const getParticipants = (applyNo) => request.get(`/api/applications/${applyNo}/participants`)
export const addParticipant = (applyNo, data) => request.post(`/api/applications/${applyNo}/participants`, data)
export const updateParticipant = (pid, data) => request.put(`/api/participants/${pid}`, data)
export const cancelParticipant = (pid) => request.post(`/api/participants/${pid}/cancel`)
export const changeResponsible = (applyNo, data) => request.post(`/api/applications/${applyNo}/change-responsible`, data)
