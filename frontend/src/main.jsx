import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { LayerProvider } from './contexts/LayerContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <LayerProvider>
      <App />
    </LayerProvider>
  </StrictMode>,
)
