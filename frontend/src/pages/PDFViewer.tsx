import React from 'react'
import { useParams } from 'react-router-dom'
import { Document, Page, pdfjs } from 'react-pdf'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function PDFViewerPage(){
  const { id } = useParams()
  const url = `/api/v1/patient/reports/download/${id}`
  return (
    <Paper sx={{p:2}}>
      <Typography variant="h6">Report {id}</Typography>
      <Document file={url}>
        <Page pageNumber={1} />
      </Document>
    </Paper>
  )
}
