import axios from 'axios';
import { API_BASE_URL } from '../config';

/**
 * Service de gestion des utilisateurs
 *
 * Endpoints disponibles (Admin uniquement) :
 * - GET /api/auth/users/ - Liste des utilisateurs
 * - GET /api/auth/users/{id}/ - Détails d'un utilisateur
 * - POST /api/auth/users/create/ - Créer un utilisateur
 * - PUT/PATCH /api/auth/users/{id}/update/ - Modifier un utilisateur
 * - DELETE /api/auth/users/{id}/delete/ - Supprimer un utilisateur
 */

const USER_API_URL = `${API_BASE_URL}/api/auth/users`;

class UserService {
  /**
   * Récupère la liste de tous les utilisateurs
   * @param {Object} filters - Filtres optionnels (role, search)
   * @returns {Promise<Array>} Liste des utilisateurs
   */
  async getUsers(filters = {}) {
    try {
      const params = new URLSearchParams();

      if (filters.role) {
        params.append('role', filters.role);
      }

      if (filters.search) {
        params.append('search', filters.search);
      }

      const queryString = params.toString();
      const url = queryString ? `${USER_API_URL}/?${queryString}` : `${USER_API_URL}/`;

      const response = await axios.get(url);
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Récupère les détails d'un utilisateur
   * @param {number} userId - ID de l'utilisateur
   * @returns {Promise<Object>} Détails de l'utilisateur
   */
  async getUser(userId) {
    try {
      const response = await axios.get(`${USER_API_URL}/${userId}/`);
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Crée un nouvel utilisateur
   * @param {Object} userData - Données de l'utilisateur
   * @param {string} userData.username - Nom d'utilisateur
   * @param {string} userData.email - Email
   * @param {string} userData.first_name - Prénom
   * @param {string} userData.last_name - Nom
   * @param {string} userData.role - Rôle (admin, contributeur, lecteur)
   * @param {string} userData.password - Mot de passe
   * @param {string} userData.password_confirm - Confirmation du mot de passe
   * @returns {Promise<Object>} Utilisateur créé
   */
  async createUser(userData) {
    try {
      const response = await axios.post(`${USER_API_URL}/create/`, userData);
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Met à jour un utilisateur
   * @param {number} userId - ID de l'utilisateur
   * @param {Object} userData - Données à modifier
   * @param {boolean} partial - Si true, utilise PATCH (modification partielle)
   * @returns {Promise<Object>} Utilisateur modifié
   */
  async updateUser(userId, userData, partial = true) {
    try {
      const method = partial ? 'patch' : 'put';
      const response = await axios[method](`${USER_API_URL}/${userId}/update/`, userData);
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Supprime un utilisateur
   * @param {number} userId - ID de l'utilisateur
   * @returns {Promise<Object>} Message de confirmation
   */
  async deleteUser(userId) {
    try {
      const response = await axios.delete(`${USER_API_URL}/${userId}/delete/`);
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Gère les erreurs d'API
   * @private
   */
  _handleError(error) {
    if (error.response) {
      const message = error.response.data?.error ||
                     error.response.data?.message ||
                     'Une erreur est survenue';

      const details = error.response.data?.details || null;

      return new Error(JSON.stringify({
        message,
        details,
        status: error.response.status
      }));
    }
    return error;
  }

  /**
   * Parse une erreur pour récupérer le message et les détails
   * @param {Error} error - Erreur à parser
   * @returns {Object} { message, details }
   */
  parseError(error) {
    try {
      const parsed = JSON.parse(error.message);
      return {
        message: parsed.message || 'Une erreur est survenue',
        details: parsed.details || null
      };
    } catch {
      return {
        message: error.message || 'Une erreur est survenue',
        details: null
      };
    }
  }
}

export default new UserService();
