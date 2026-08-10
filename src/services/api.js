// Centralized API service for frontend
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken(){
  return localStorage.getItem('cervival_token');
}
function setToken(token){
  if(token) localStorage.setItem('cervival_token', token);
  else localStorage.removeItem('cervival_token');
}

async function request(path, opts = {}) {
  const headers = opts.headers || {};
  const token = getToken();
  if(token){
    headers['Authorization'] = `Bearer ${token}`;
  }
  opts.headers = headers;

  const res = await fetch(API_URL + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || JSON.stringify(data));
  return data;
}

export async function signup(name, email, password) {
  return request('/api/auth/signup', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({name,email,password})});
}

export async function login(email, password) {
  return request('/api/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,password})});
}

export async function verifyOtp(temp_token, otp) {
  // backend expects token and otp as query parameters
  const res = await fetch(`${API_URL}/api/auth/verify-otp?token=${encodeURIComponent(temp_token)}&otp=${encodeURIComponent(otp)}`, {method: 'POST'});
  const data = await res.json().catch(() => ({}));
  if(!res.ok) throw new Error(data.detail || data.message || JSON.stringify(data));
  // store access token
  if(data.access_token) setToken(data.access_token);
  return data;
}

export async function me(){
  return request('/api/auth/me');
}

export async function createPatient(payload){
  return request('/api/patients/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
}

export async function listPatients(){
  return request('/api/patients/');
}

export async function createCase(payload){
  return request('/api/cases/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
}

export async function uploadImage(case_id, file){
  const form = new FormData();
  form.append('file', file);
  const token = getToken();
  const headers = {};
  if(token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_URL}/api/cases/${case_id}/image`, {method:'POST', body: form, headers});
  if (!res.ok) {
    const err = await res.json().catch(()=>({}));
    throw new Error(err.detail || 'Image upload failed');
  }
  return res.json();
}

export async function predict(case_id, data){
  return request('/api/predictions/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({case_id, data})});
}

export function logout(){
  setToken(null);
}

export default {signup, login, verifyOtp, createPatient, createCase, uploadImage, predict, me, listPatients, logout};
