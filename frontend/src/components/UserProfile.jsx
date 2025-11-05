import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './UserProfile.css';

/**
 * Composant de profil utilisateur
 *
 * Permet à tout utilisateur authentifié de modifier :
 * - Email
 * - Prénom / Nom
 * - Mot de passe
 */
const UserProfile = () => {
  const { user } = useAuth();

  // État du formulaire
  const [formData, setFormData] = useState({
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    password: '',
    password_confirm: ''
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  // Gérer les changements de champs
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));

    // Effacer l'erreur du champ modifié
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // Valider le formulaire
  const validate = () => {
    const newErrors = {};

    // Email optionnel mais doit être valide si fourni
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "L'email n'est pas valide";
    }

    // Validation du mot de passe si fourni
    if (formData.password) {
      if (formData.password.length < 20) {
        newErrors.password = 'Le mot de passe doit contenir au moins 20 caractères';
      }

      if (formData.password !== formData.password_confirm) {
        newErrors.password_confirm = 'Les mots de passe ne correspondent pas';
      }
    }

    // Vérifier la confirmation même si mot de passe vide
    if (formData.password_confirm && !formData.password) {
      newErrors.password = 'Veuillez entrer un mot de passe';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Soumettre le formulaire
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Préparer les données à envoyer
      const dataToSubmit = { ...formData };

      // Ne pas envoyer le mot de passe s'il est vide
      if (!dataToSubmit.password) {
        delete dataToSubmit.password;
        delete dataToSubmit.password_confirm;
      }

      // Mettre à jour le profil
      const response = await axios.patch(`${API_BASE_URL}/api/auth/profile/`, dataToSubmit);

      setSuccess('Profil mis à jour avec succès');

      // Si le mot de passe a été changé, reconnecter l'utilisateur
      if (formData.password) {
        // Réinitialiser les champs de mot de passe
        setFormData((prev) => ({
          ...prev,
          password: '',
          password_confirm: ''
        }));

        setSuccess('Profil et mot de passe mis à jour avec succès. Vous allez être redirigé...');

        // Attendre 2 secondes puis rediriger vers login
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      } else {
        // Mettre à jour les données dans le formulaire
        setFormData({
          email: response.data.email || '',
          first_name: response.data.first_name || '',
          last_name: response.data.last_name || '',
          password: '',
          password_confirm: ''
        });

        // Effacer le message de succès après 3 secondes
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      // Gérer les erreurs de validation du backend
      if (err.response?.data?.details) {
        setErrors(err.response.data.details);
      } else {
        setError(err.response?.data?.error || 'Une erreur est survenue');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="user-profile">
      <div className="profile-container">
        <div className="profile-header">
          <h2>Mon profil</h2>
          <p className="profile-subtitle">
            Gérez vos informations personnelles et votre mot de passe
          </p>
        </div>

        <div className="profile-info-card">
          <h3>Informations du compte</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Nom d'utilisateur</span>
              <span className="info-value">{user?.username}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Rôle</span>
              <span className={`role-badge ${user?.role}`}>
                {user?.role_display}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Membre depuis</span>
              <span className="info-value">
                {user?.date_joined
                  ? new Date(user.date_joined).toLocaleDateString('fr-FR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })
                  : '-'}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Dernière connexion</span>
              <span className="info-value">
                {user?.last_login
                  ? new Date(user.last_login).toLocaleString('fr-FR', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })
                  : '-'}
              </span>
            </div>
          </div>
        </div>

        <div className="profile-form-card">
          <h3>Modifier mes informations</h3>

          {/* Messages */}
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <form className="profile-form" onSubmit={handleSubmit}>
            {/* Email */}
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={errors.email ? 'error' : ''}
                placeholder="votre.email@example.com"
              />
              {errors.email && <div className="form-error">{errors.email}</div>}
            </div>

            {/* Prénom */}
            <div className="form-group">
              <label htmlFor="first_name">Prénom</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                placeholder="John"
              />
            </div>

            {/* Nom */}
            <div className="form-group">
              <label htmlFor="last_name">Nom</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                placeholder="Doe"
              />
            </div>

            <div className="form-divider">
              <span>Changer le mot de passe</span>
            </div>

            {/* Mot de passe */}
            <div className="form-group">
              <label htmlFor="password">Nouveau mot de passe</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={errors.password ? 'error' : ''}
                placeholder="Laisser vide pour ne pas modifier"
              />
              {errors.password && <div className="form-error">{errors.password}</div>}
              {!errors.password && (
                <div className="form-help">
                  Laisser vide pour conserver votre mot de passe actuel
                </div>
              )}
            </div>

            {/* Confirmation mot de passe */}
            <div className="form-group">
              <label htmlFor="password_confirm">Confirmer le nouveau mot de passe</label>
              <input
                type="password"
                id="password_confirm"
                name="password_confirm"
                value={formData.password_confirm}
                onChange={handleChange}
                className={errors.password_confirm ? 'error' : ''}
                placeholder="Confirmer le mot de passe"
              />
              {errors.password_confirm && (
                <div className="form-error">{errors.password_confirm}</div>
              )}
            </div>

            {formData.password && (
              <div className="password-warning">
                ⚠️ Si vous changez votre mot de passe, vous devrez vous reconnecter.
              </div>
            )}

            {/* Boutons */}
            <div className="form-actions">
              <button type="submit" className="btn-submit" disabled={loading}>
                {loading ? 'Enregistrement...' : 'Enregistrer les modifications'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
