import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import Login from './components/Login.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { LayerProvider } from './contexts/LayerContext'
import { AuthProvider } from './contexts/AuthContext'
import { setupAxiosInterceptors } from './services/auth/axiosInterceptor'

// Configurer les intercepteurs Axios pour gérer l'authentification
// Rediriger automatiquement vers /login si l'utilisateur n'est plus authentifié
setupAxiosInterceptors(() => {
  // Rediriger vers la page de login
  window.location.href = '/login';
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <LayerProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <App />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </LayerProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
