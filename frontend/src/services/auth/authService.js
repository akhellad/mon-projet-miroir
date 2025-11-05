import axios from 'axios';
import { API_BASE_URL } from '../../config';

/**
 * Service d'authentification abstrait.
 *
 * Architecture flexible permettant de basculer facilement entre
 * JWT et OpenID Connect en modifiant uniquement ce fichier.
 */

const AUTH_API_URL = `${API_BASE_URL}/api/auth`;

// Clés de stockage
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user';

/**
 * Service d'authentification
 */
class AuthService {
  /**
   * Connexion utilisateur
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{user, tokens}>}
   */
  async login(username, password) {
    try {
      const response = await axios.post(`${AUTH_API_URL}/login/`, {
        username,
        password
      });

      const { user, tokens } = response.data;

      // Stocker les tokens et les infos utilisateur
      this.setTokens(tokens.access_token, tokens.refresh_token);
      this.setUser(user);

      return { user, tokens };
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Déconnexion utilisateur
   */
  async logout() {
    try {
      const refreshToken = this.getRefreshToken();

      if (refreshToken) {
        // Appeler l'API pour révoquer le refresh token
        await axios.post(
          `${AUTH_API_URL}/logout/`,
          { refresh_token: refreshToken },
          { headers: this._getAuthHeaders() }
        );
      }
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    } finally {
      // Nettoyer le localStorage dans tous les cas
      this.clearAuth();
    }
  }

  /**
   * Rafraîchit l'access token
   * @returns {Promise<string>} Nouveau access token
   */
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();

    if (!refreshToken) {
      throw new Error('Aucun refresh token disponible');
    }

    try {
      const response = await axios.post(`${AUTH_API_URL}/refresh/`, {
        refresh_token: refreshToken
      });

      const { access_token } = response.data;
      this.setAccessToken(access_token);

      return access_token;
    } catch (error) {
      // Si le refresh échoue, déconnecter l'utilisateur
      this.clearAuth();
      throw this._handleError(error);
    }
  }

  /**
   * Récupère les informations de l'utilisateur connecté
   * @returns {Promise<Object>} Données utilisateur
   */
  async getCurrentUser() {
    try {
      const response = await axios.get(`${AUTH_API_URL}/me/`, {
        headers: this._getAuthHeaders()
      });

      const user = response.data;
      this.setUser(user);

      return user;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Vérifie si l'utilisateur est authentifié
   * @returns {boolean}
   */
  isAuthenticated() {
    return !!this.getAccessToken();
  }

  /**
   * Récupère l'utilisateur depuis le localStorage
   * @returns {Object|null}
   */
  getUser() {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  /**
   * Récupère l'access token
   * @returns {string|null}
   */
  getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  /**
   * Récupère le refresh token
   * @returns {string|null}
   */
  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  /**
   * Stocke les tokens
   */
  setTokens(accessToken, refreshToken) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }

  /**
   * Stocke uniquement l'access token
   */
  setAccessToken(accessToken) {
    localStorage.setItem(TOKEN_KEY, accessToken);
  }

  /**
   * Stocke les informations utilisateur
   */
  setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  /**
   * Nettoie toutes les données d'authentification
   */
  clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  /**
   * Génère les headers d'authentification
   * @returns {Object}
   */
  _getAuthHeaders() {
    const token = this.getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /**
   * Gère les erreurs d'API
   */
  _handleError(error) {
    if (error.response) {
      const message = error.response.data?.error ||
                     error.response.data?.message ||
                     'Une erreur est survenue';
      return new Error(message);
    }
    return error;
  }

  /**
   * Vérifie si l'utilisateur a un rôle spécifique
   * @param {string} role - 'admin', 'contributeur', ou 'lecteur'
   * @returns {boolean}
   */
  hasRole(role) {
    const user = this.getUser();
    if (!user) return false;

    const roleHierarchy = {
      admin: ['admin'],
      contributeur: ['admin', 'contributeur'],
      lecteur: ['admin', 'contributeur', 'lecteur']
    };

    return roleHierarchy[role]?.includes(user.role) || false;
  }

  /**
   * Vérifie si l'utilisateur est admin
   * @returns {boolean}
   */
  isAdmin() {
    return this.hasRole('admin');
  }

  /**
   * Vérifie si l'utilisateur est contributeur ou admin
   * @returns {boolean}
   */
  isContributeur() {
    return this.hasRole('contributeur');
  }
}

export default new AuthService();
