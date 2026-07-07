import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './style.css'
import 'maplibre-gl/dist/maplibre-gl.css'

// NOTE: no React.StrictMode — its dev double-mount creates/destroys the
// MapLibre map twice and can leave a blank WebGL canvas.
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
