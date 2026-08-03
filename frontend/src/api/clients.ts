import axios from './axios'

export const authApi = {
  login: (payload: {username:string,password:string}) => axios.post('/auth/login', payload),
  me: () => axios.get('/auth/me')
}

export const patientApi = {
  profile: () => axios.get('/patient/profile'),
  history: (params?:any) => axios.get('/patient/history', {params}),
  reports: (params?:any) => axios.get('/patient/reports', {params}),
  downloadReport: (id:number) => axios.get(`/patient/reports/download/${id}`, {responseType: 'blob'})
}

export const doctorApi = {
  patients: (params?:any) => axios.get('/doctor/patients', {params}),
  reports: (params?:any) => axios.get('/doctor/reports', {params}),
}

export const analysisApi = {
  get: (id:number)=> axios.get(`/analysis/${id}`),
  gradcam: (id:number)=> axios.get(`/analysis/${id}/gradcam`),
  explain: (id:number)=> axios.get(`/analysis/${id}/explanation`)
}

export const visualizationApi = {
  generate: (analysis_id:number) => axios.post(`/visualization/generate/${analysis_id}`),
  get: (id:number) => axios.get(`/visualization/${id}`),
  download: (id:number) => axios.get(`/visualization/download/${id}`, {responseType: 'blob'})
}

export const modelsApi = {
  list: ()=> axios.get('/models'),
  activate: (id:number)=> axios.post(`/models/activate/${id}`)
}
