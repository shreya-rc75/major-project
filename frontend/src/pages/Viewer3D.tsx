import React, { Suspense } from 'react'
import { useParams } from 'react-router-dom'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF } from '@react-three/drei'

function Model({url}:{url:string}){
  const { scene } = useGLTF(url as any)
  return <primitive object={scene} />
}

export default function Viewer3D(){
  const { id } = useParams()
  const url = `/api/v1/visualization/${id}` // we'll fetch metadata to get mesh_url in real app
  return (
    <Paper sx={{p:2}}>
      <Typography variant="h6">3D Viewer</Typography>
      <div style={{height:600}}>
        <Canvas>
          <ambientLight />
          <pointLight position={[10,10,10]} />
          <Suspense fallback={null}>
            {/* placeholder - in real flow fetch GLB URL and pass to Model */}
          </Suspense>
          <OrbitControls />
        </Canvas>
      </div>
    </Paper>
  )
}
