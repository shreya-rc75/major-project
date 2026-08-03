import React from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import axios from '../api/axios'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

export default function PatientDetail(){
  const { id } = useParams()
  const { data, isLoading } = useQuery(['patient', id], ()=> axios.get(`/doctor/patient/${id}`).then(r=>r.data))
  if(isLoading) return <Typography>Loading...</Typography>
  return (
    <Paper sx={{p:2}}>
      <Typography variant="h6">Patient Detail</Typography>
      <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(data, null, 2)}</pre>
    </Paper>
  )
}
