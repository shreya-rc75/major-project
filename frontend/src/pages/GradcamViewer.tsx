import React from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { analysisApi } from '../api/clients'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

export default function GradcamViewer(){
  const { id } = useParams()
  const { data, isLoading } = useQuery(['gradcam', id], ()=> analysisApi.gradcam(Number(id)).then(r=>r.data))
  if(isLoading) return <Typography>Loading...</Typography>
  const url = data?.gradcam_url
  return (
    <Paper sx={{p:2}}>
      <Typography variant="h6">Grad-CAM</Typography>
      {url ? <img src={url} alt="gradcam" style={{maxWidth:'100%'}} /> : <Typography>No GradCAM available</Typography>}
    </Paper>
  )
}
