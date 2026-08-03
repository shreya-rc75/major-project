import React from 'react'
import Paper from '@mui/material/Paper'
import Skeleton from '@mui/material/Skeleton'

export default function SkeletonLoader(){
  return (
    <Paper sx={{p:2}}>
      <Skeleton variant="rectangular" height={200} />
      <Skeleton />
      <Skeleton />
    </Paper>
  )
}
