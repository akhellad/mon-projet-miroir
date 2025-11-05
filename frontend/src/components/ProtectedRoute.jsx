import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Composant ProtectedRoute
 *
 * Protège les routes nécessitant une authentification.
 * Redirige vers /login si l'utilisateur n'est pas connecté.
 *
 * Usage:
 *   <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
 *   <Route path="/admin" element={<ProtectedRoute requiredRole="admin"><AdminPage /></ProtectedRoute>} />
 */
const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { isAuthenticated, loading, hasRole } = useAuth();

  // Afficher un loader pendant la vérification de l'auth
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '18px',
        color: '#667eea'
      }}>
        Chargement...
      </div>
    );
  }

  // Rediriger vers login si non authentifié
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Vérifier le rôle requis si spécifié
  if (requiredRole && !hasRole(requiredRole)) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <h2>Accès refusé</h2>
        <p>Vous n'avez pas les permissions nécessaires pour accéder à cette page.</p>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;
