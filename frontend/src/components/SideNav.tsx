import React from 'react'
import Drawer from '@mui/material/Drawer'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import HomeIcon from '@mui/icons-material/Home'
import UploadIcon from '@mui/icons-material/Upload'
import PeopleIcon from '@mui/icons-material/People'
import SettingsIcon from '@mui/icons-material/Settings'
import { Link as RouterLink } from 'react-router-dom'

const drawerWidth = 240

export default function SideNav(){
  return (
    <Drawer variant="permanent" sx={{width:drawerWidth, [`& .MuiDrawer-paper`]: {width: drawerWidth, boxSizing: 'border-box', mt:8}}}>
      <List>
        <ListItem button component={RouterLink} to="/">
          <ListItemIcon><HomeIcon/></ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        <ListItem button component={RouterLink} to="/upload">
          <ListItemIcon><UploadIcon/></ListItemIcon>
          <ListItemText primary="Upload" />
        </ListItem>
        <ListItem button component={RouterLink} to="/patients">
          <ListItemIcon><PeopleIcon/></ListItemIcon>
          <ListItemText primary="Patients" />
        </ListItem>
        <ListItem button component={RouterLink} to="/settings">
          <ListItemIcon><SettingsIcon/></ListItemIcon>
          <ListItemText primary="Settings" />
        </ListItem>
      </List>
    </Drawer>
  )
}
