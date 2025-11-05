import { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/auth/authService';

/**
 * Context d'authentification
 *
 * Fournit l'état d'authentification global et les méthodes
 * de connexion/déconnexion à toute l'application.
 */

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Initialiser l'état d'authentification au chargement
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          // Vérifier que le token est valide en appelant l'API /me/
          try {
            const userData = await authService.getCurrentUser();
            setUser(userData);
            setIsAuthenticated(true);
          } catch (error) {
            // Token invalide ou utilisateur supprimé
            console.warn('Token invalide ou utilisateur inexistant, nettoyage...');
            authService.clearAuth();
            setUser(null);
            setIsAuthenticated(false);
          }
        }
      } catch (error) {
        console.error('Erreur d\'initialisation de l\'auth:', error);
        authService.clearAuth();
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []); // Pas de dépendance - s'exécute une seule fois au montage

  /**
   * Connexion
   */
  const login = async (username, password) => {
    try {
      const { user: loggedUser } = await authService.login(username, password);
      setUser(loggedUser);
      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Erreur de connexion'
      };
    }
  };

  /**
   * Déconnexion
   */
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  /**
   * Rafraîchir le token
   */
  const refreshToken = async () => {
    try {
      await authService.refreshAccessToken();
      return true;
    } catch (error) {
      console.error('Erreur de rafraîchissement du token:', error);
      handleLogout();
      return false;
    }
  };

  /**
   * Gérer la déconnexion (sans appel API)
   */
  const handleLogout = () => {
    authService.clearAuth();
    setUser(null);
    setIsAuthenticated(false);
  };

  /**
   * Vérifier les permissions
   */
  const hasRole = (role) => {
    return authService.hasRole(role);
  };

  const isAdmin = () => {
    return authService.isAdmin();
  };

  const isContributeur = () => {
    return authService.isContributeur();
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    refreshToken,
    hasRole,
    isAdmin,
    isContributeur
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Hook pour utiliser le context d'authentification
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth doit être utilisé à l\'intérieur d\'un AuthProvider');
  }
  return context;
};

export default AuthContext;
