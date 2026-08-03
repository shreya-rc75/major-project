import React, { useState } from 'react'
import Paper from '@mui/material/Paper'
import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import axios from '../api/axios'

export default function Upload(){
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  const submit = async ()=>{
    if(!file) return
    const fd = new FormData()
    fd.append('file', file)
    try{
      setStatus('Uploading...')
      const r = await axios.post('/upload', fd, {headers: {'Content-Type': 'multipart/form-data'}})
      setStatus('Upload queued')
    }catch(e:any){
      setStatus('Failed: ' + (e?.response?.data?.detail || e.message))
    }
  }

  return (
    <Paper sx={{p:2}}>
      <Typography variant="h6">Upload Image</Typography>
      <Box sx={{mt:2}}>
        <input type="file" onChange={(e)=> setFile(e.target.files?.[0] ?? null)} />
      </Box>
      <Button variant="contained" sx={{mt:2}} onClick={submit}>Upload</Button>
      {status && <Typography sx={{mt:1}}>{status}</Typography>}
    </Paper>
  )
}
