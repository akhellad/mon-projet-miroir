import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import userService from '../services/userService';
import UserCreateModal from './UserCreateModal';
import UserFormModal from './UserFormModal';
import DeleteConfirmModal from './DeleteConfirmModal';
import './UserManagement.css';

/**
 * Composant de gestion des utilisateurs
 *
 * Fonctionnalités :
 * - Liste des utilisateurs avec filtres (rôle, recherche)
 * - Création d'utilisateurs
 * - Modification d'utilisateurs
 * - Suppression d'utilisateurs
 * - Réservé aux administrateurs uniquement
 */
const UserManagement = () => {
  const { user: currentUser } = useAuth();

  // État
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Filtres
  const [roleFilter, setRoleFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modales
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [deletingUser, setDeletingUser] = useState(null);

  // Charger les utilisateurs
  useEffect(() => {
    loadUsers();
  }, [roleFilter, searchQuery]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const filters = {};
      if (roleFilter) filters.role = roleFilter;
      if (searchQuery) filters.search = searchQuery;

      const data = await userService.getUsers(filters);
      setUsers(data);
    } catch (err) {
      const { message } = userService.parseError(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // Gestionnaires d'événements
  const handleCreateUser = async (userData) => {
    try {
      setError(null);
      const createdUser = await userService.createUser(userData);
      setSuccess('Utilisateur créé avec succès');
      loadUsers();

      // Retourner l'utilisateur créé avec le mot de passe généré
      return createdUser;
    } catch (err) {
      const { message, details } = userService.parseError(err);
      throw new Error(details ? JSON.stringify(details) : message);
    }
  };

  const handleUpdateUser = async (userData) => {
    try {
      setError(null);
      await userService.updateUser(editingUser.id, userData, true);
      setSuccess('Utilisateur modifié avec succès');
      setEditingUser(null);
      loadUsers();

      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      const { message, details } = userService.parseError(err);
      throw new Error(details ? JSON.stringify(details) : message);
    }
  };

  const handleDeleteUser = async () => {
    try {
      setError(null);
      await userService.deleteUser(deletingUser.id);
      setSuccess(`Utilisateur "${deletingUser.username}" supprimé avec succès`);
      setDeletingUser(null);
      loadUsers();

      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      const { message } = userService.parseError(err);
      setError(message);
      setDeletingUser(null);
    }
  };

  // Formater la date
  const formatDate = (dateString) => {
    if (!dateString) return 'Jamais';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Affichage du rôle
  const getRoleLabel = (role) => {
    const labels = {
      admin: 'Administrateur',
      contributeur: 'Contributeur',
      lecteur: 'Lecteur'
    };
    return labels[role] || role;
  };

  return (
    <div className="user-management">
      {/* Header */}
      <div className="user-management-header">
        <h2>Gestion des utilisateurs</h2>

        <div className="user-filters">
          <input
            type="text"
            className="search-input"
            placeholder="Rechercher par nom, email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <select
            className="role-filter"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
          >
            <option value="">Tous les rôles</option>
            <option value="admin">Administrateurs</option>
            <option value="contributeur">Contributeurs</option>
            <option value="lecteur">Lecteurs</option>
          </select>

          <button
            className="btn-create-user"
            onClick={() => setShowCreateModal(true)}
          >
            + Créer un utilisateur
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {/* Tableau des utilisateurs */}
      {loading ? (
        <div className="loading-state">Chargement des utilisateurs...</div>
      ) : users.length === 0 ? (
        <div className="empty-state">
          <h3>Aucun utilisateur trouvé</h3>
          <p>
            {searchQuery || roleFilter
              ? 'Essayez de modifier vos filtres de recherche'
              : 'Créez votre premier utilisateur pour commencer'}
          </p>
        </div>
      ) : (
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>Utilisateur</th>
                <th>Email</th>
                <th>Rôle</th>
                <th>Statut</th>
                <th>Dernière connexion</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div>
                      <strong>{user.username}</strong>
                      {user.first_name && user.last_name && (
                        <div style={{ fontSize: '12px', color: '#64748b' }}>
                          {user.first_name} {user.last_name}
                        </div>
                      )}
                    </div>
                  </td>
                  <td>{user.email || '-'}</td>
                  <td>
                    <span className={`role-badge ${user.role}`}>
                      {getRoleLabel(user.role)}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? 'Actif' : 'Inactif'}
                    </span>
                  </td>
                  <td>{formatDate(user.last_login)}</td>
                  <td>
                    <div className="user-actions">
                      <button
                        className="btn-edit"
                        onClick={() => setEditingUser(user)}
                      >
                        Modifier
                      </button>
                      <button
                        className="btn-delete"
                        onClick={() => setDeletingUser(user)}
                        disabled={user.id === currentUser?.id}
                        title={
                          user.id === currentUser?.id
                            ? 'Vous ne pouvez pas supprimer votre propre compte'
                            : 'Supprimer cet utilisateur'
                        }
                      >
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modales */}
      {showCreateModal && (
        <UserCreateModal
          onSubmit={handleCreateUser}
          onClose={() => setShowCreateModal(false)}
        />
      )}

      {editingUser && (
        <UserFormModal
          title="Modifier l'utilisateur"
          user={editingUser}
          onSubmit={handleUpdateUser}
          onClose={() => setEditingUser(null)}
        />
      )}

      {deletingUser && (
        <DeleteConfirmModal
          user={deletingUser}
          onConfirm={handleDeleteUser}
          onClose={() => setDeletingUser(null)}
        />
      )}
    </div>
  );
};

export default UserManagement;
