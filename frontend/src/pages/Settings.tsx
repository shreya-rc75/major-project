import React from 'react'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

export default function Settings(){
  return (
    <Paper sx={{p:2}}>
      <Typography variant="h6">Settings</Typography>
      <Typography>Account and preferences</Typography>
    </Paper>
  )
}
