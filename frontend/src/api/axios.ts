import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'

const axiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
})

// attach token if present
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token && config.headers) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

export default axiosInstance
