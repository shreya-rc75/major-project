import React from 'react'
import { createTheme, ThemeProvider, CssBaseline } from '@mui/material'
import { useLocalStorage } from '../hooks/useAuth'

export const ThemeProviderWrapper: React.FC<{children: React.ReactNode}> = ({children})=>{
  const [darkMode] = useLocalStorage<boolean>('darkMode', true)
  const theme = React.useMemo(()=> createTheme({palette: {mode: darkMode ? 'dark' : 'light'}}), [darkMode])
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  )
}
