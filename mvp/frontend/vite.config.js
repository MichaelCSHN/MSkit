import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import cesium from 'vite-plugin-cesium'

// Proxy /api to the FastAPI backend so the frontend has no CORS concerns.
export default defineConfig({
  plugins: [react(), cesium()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  // multi-page: main app (index.html) + standalone NRW 3D flythrough (nrw3d.html)
  build: {
    rollupOptions: {
      input: { main: 'index.html', nrw3d: 'nrw3d.html' },
    },
  },
})
