import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

/**
 * Vite configuration for iHub AI Character Assistant
 * 
 * Configures React with Tailwind CSS and environment variable support.
 */
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: false
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser'
  },
  // Environment variables - can be set in .env files or at build time
  // Example .env file:
  // VITE_BACKEND_API=http://api.example.com:8000
  // VITE_BACKEND_API_WS=ws://api.example.com:8000
})
