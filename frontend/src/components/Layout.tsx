import React from 'react'
import { Outlet } from 'react-router-dom'
import Box from '@mui/material/Box'
import CssBaseline from '@mui/material/CssBaseline'
import TopBar from './NavBar'
import SideNav from './SideNav'

export default function Layout(){
  return (
    <Box sx={{display:'flex'}}>
      <CssBaseline />
      <TopBar />
      <SideNav />
      <Box component="main" sx={{flexGrow:1, p:3, mt:8}}>
        <Outlet />
      </Box>
    </Box>
  )
}
