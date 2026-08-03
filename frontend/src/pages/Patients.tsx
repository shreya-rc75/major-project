import React from 'react'
import { useQuery } from 'react-query'
import { doctorApi } from '../api/clients'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'

export default function Patients(){
  const { data, isLoading } = useQuery('patients', ()=> doctorApi.patients().then(r=>r.data))
  if(isLoading) return <Typography>Loading...</Typography>
  return (
    <Paper sx={{p:2}}>
      <Typography variant="h6">Patients</Typography>
      <List>
        {(data || []).map((p:any)=> (
          <ListItem key={p.id} button component="a" href={`/patients/${p.id}`}>
            <ListItemText primary={p.full_name || p.patient_identifier} secondary={p.id} />
          </ListItem>
        ))}
      </List>
    </Paper>
  )
}
