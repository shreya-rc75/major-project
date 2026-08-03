import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import App from './App'
import { ThemeProviderWrapper } from './components/ThemeProvider'
import './styles.css'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProviderWrapper>
          <App />
        </ThemeProviderWrapper>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
