import React from 'react'
import Grid from '@mui/material/Grid'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { useQuery } from 'react-query'
import { patientApi } from '../api/clients'
import SkeletonLoader from '../components/SkeletonLoader'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function Dashboard(){
  const { data, isLoading } = useQuery('riskHistory', ()=> patientApi.history().then(r=>r.data), {staleTime: 1000*60})

  if(isLoading) return <SkeletonLoader />

  const sample = (data && Array.isArray(data) && data.slice(0,10).map((d:any, idx:number)=>({name: `A${idx}`, value: d.probabilities?.A || 0}))) || []

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={8}>
        <Paper sx={{p:2}}>
          <Typography variant="h6">Recent Analyses</Typography>
          {/* placeholder table or list */}
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper sx={{p:2}}>
          <Typography variant="h6">Risk Trend</Typography>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={sample}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>
    </Grid>
  )
}
