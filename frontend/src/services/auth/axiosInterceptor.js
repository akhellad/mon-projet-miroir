import axios from 'axios';
import authService from './authService';

/**
 * Intercepteur Axios pour gérer automatiquement l'authentification
 *
 * - Injecte le token JWT dans tous les requêtes
 * - Gère le refresh automatique des tokens expirés
 * - Redirige vers login si le refresh échoue
 */

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

/**
 * Configure les intercepteurs Axios
 */
export const setupAxiosInterceptors = (onUnauthenticated) => {
  // Intercepteur de requête : injecter le token
  axios.interceptors.request.use(
    (config) => {
      const token = authService.getAccessToken();

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Intercepteur de réponse : gérer le refresh token
  axios.interceptors.response.use(
    (response) => {
      return response;
    },
    async (error) => {
      const originalRequest = error.config;

      // Ne pas essayer de refresh pour les endpoints de login et refresh eux-mêmes
      const isAuthEndpoint = originalRequest.url?.includes('/api/auth/login') ||
                            originalRequest.url?.includes('/api/auth/refresh');

      // Si l'erreur est 401 et qu'on n'a pas encore essayé de refresh
      if (error.response?.status === 401 && !originalRequest._retry) {
        // Si c'est un endpoint d'authentification, ne pas intercepter
        if (isAuthEndpoint) {
          return Promise.reject(error);
        }

        // Vérifier si c'est une erreur "Token invalide" ou "Compte désactivé"
        const errorMessage = error.response?.data?.detail || '';
        const isTokenInvalid = errorMessage.includes('Token invalide') ||
                              errorMessage.includes('Compte désactivé') ||
                              errorMessage.includes('Utilisateur');

        // Si le token est invalide ou l'utilisateur n'existe plus, ne pas essayer de refresh
        if (isTokenInvalid) {
          console.warn('Token invalide ou utilisateur inexistant, redirection vers login...');
          authService.clearAuth();

          if (onUnauthenticated) {
            onUnauthenticated();
          }

          return Promise.reject(error);
        }

        if (isRefreshing) {
          // Si un refresh est déjà en cours, mettre la requête en file d'attente
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then(token => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return axios(originalRequest);
            })
            .catch(err => {
              return Promise.reject(err);
            });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          // Tenter de rafraîchir le token
          const newToken = await authService.refreshAccessToken();
          processQueue(null, newToken);

          // Réessayer la requête originale avec le nouveau token
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return axios(originalRequest);
        } catch (refreshError) {
          // Le refresh a échoué, déconnecter l'utilisateur
          processQueue(refreshError, null);
          authService.clearAuth();

          // Callback pour rediriger vers la page de login
          if (onUnauthenticated) {
            onUnauthenticated();
          }

          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      return Promise.reject(error);
    }
  );
};

export default setupAxiosInterceptors;
