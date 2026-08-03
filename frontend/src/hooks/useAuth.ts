import { useState, useEffect } from 'react'

export function useLocalStorage<T>(key:string, initialValue:T){
  const [state, setState] = useState<T>(()=>{
    try{
      const v = localStorage.getItem(key)
      return v ? JSON.parse(v) as T : initialValue
    }catch{ return initialValue }
  })
  useEffect(()=>{
    localStorage.setItem(key, JSON.stringify(state))
  },[key,state])
  return [state, setState] as const
}

export function useAuth(){
  const token = localStorage.getItem('token')
  const isAuthenticated = !!token
  return { isAuthenticated }
}
