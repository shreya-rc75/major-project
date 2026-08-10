// Centralized API service for frontend
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, opts = {}) {
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
  // backend expects token and otp as form fields in query body
  return request(`/api/auth/verify-otp?token=${encodeURIComponent(temp_token)}&otp=${encodeURIComponent(otp)}`);
}

export async function createPatient(payload){
  return request('/api/patients/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
}

export async function createCase(payload){
  return request('/api/cases/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
}

export async function uploadImage(case_id, file){
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_URL}/api/cases/${case_id}/image`, {method:'POST', body: form});
  if (!res.ok) throw new Error('Image upload failed');
  return res.json();
}

export async function predict(case_id, data){
  return request('/api/predictions/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({case_id, data})});
}
