import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Patients from './pages/Patients'
import PatientDetail from './pages/PatientDetail'
import AnalysisPage from './pages/Analysis'
import GradcamViewer from './pages/GradcamViewer'
import Viewer3D from './pages/Viewer3D'
import PDFViewerPage from './pages/PDFViewer'
import Settings from './pages/Settings'
import { useAuth } from './hooks/useAuth'

export default function App(){
  const { isAuthenticated } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={<Login/>} />
      <Route path="/" element={isAuthenticated ? <Layout/> : <Navigate to="/login" />}>
        <Route index element={<Dashboard/>} />
        <Route path="upload" element={<Upload/>} />
        <Route path="patients" element={<Patients/>} />
        <Route path="patients/:id" element={<PatientDetail/>} />
        <Route path="analysis/:id" element={<AnalysisPage/>} />
        <Route path="gradcam/:id" element={<GradcamViewer/>} />
        <Route path="3d/:id" element={<Viewer3D/>} />
        <Route path="report/:id" element={<PDFViewerPage/>} />
        <Route path="settings" element={<Settings/>} />
      </Route>
    </Routes>
  )
}
