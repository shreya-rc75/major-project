import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Avatar from '@mui/material/Avatar'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import axios from '../api/axios'

export default function Login(){
  const nav = useNavigate()
  const [username, setUser] = useState('')
  const [password, setPass] = useState('')
  const [error, setError] = useState<string | null>(null)

  const submit = async ()=>{
    try{
      // try login endpoint; backend should support /auth/login
      const r = await axios.post('/auth/login', {username, password})
      const token = r.data.access_token || r.data.token
      if(token){
        localStorage.setItem('token', token)
        nav('/')
      }else{
        setError('Invalid login response')
      }
    }catch(e:any){
      setError(e?.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <Box sx={{display:'flex',height:'100vh',alignItems:'center',justifyContent:'center'}}>
      <Paper sx={{p:4,width:360}}>
        <Box sx={{display:'flex',flexDirection:'column',alignItems:'center',mb:2}}>
          <Avatar sx={{m:1}} />
          <Typography variant="h6">Sign in</Typography>
        </Box>
        {error && <Typography color="error">{error}</Typography>}
        <TextField label="Username" fullWidth sx={{mt:2}} value={username} onChange={(e)=>setUser(e.target.value)} />
        <TextField label="Password" type="password" fullWidth sx={{mt:2}} value={password} onChange={(e)=>setPass(e.target.value)} />
        <Button variant="contained" fullWidth sx={{mt:3}} onClick={submit}>Sign in</Button>
      </Paper>
    </Box>
  )
}
