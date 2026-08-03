import React from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { analysisApi } from '../api/clients'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

export default function AnalysisPage(){
  const { id } = useParams()
  const { data, isLoading } = useQuery(['analysis', id], ()=> analysisApi.get(Number(id)).then(r=>r.data))
  if(isLoading) return <Typography>Loading...</Typography>
  return (
    <Paper sx={{p:2}}>
      <Typography variant="h6">Analysis {id}</Typography>
      <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(data, null, 2)}</pre>
    </Paper>
  )
}
