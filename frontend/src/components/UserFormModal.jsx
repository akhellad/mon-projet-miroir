import { useState, useEffect } from 'react';
import './UserManagement.css';

/**
 * Modal de formulaire pour créer ou modifier un utilisateur
 *
 * Props:
 * - title: Titre du modal
 * - user: Utilisateur à modifier (optionnel, si absent = création)
 * - onSubmit: Callback pour soumettre le formulaire
 * - onClose: Callback pour fermer le modal
 */
const UserFormModal = ({ title, user, onSubmit, onClose }) => {
  const isEditMode = !!user;

  // État du formulaire
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'lecteur',
    is_active: true,
    password: '',
    password_confirm: ''
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  // Charger les données de l'utilisateur en mode édition
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        role: user.role || 'lecteur',
        is_active: user.is_active !== false,
        password: '',
        password_confirm: ''
      });
    }
  }, [user]);

  // Gérer les changements de champs
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
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

    // Username requis en mode création
    if (!isEditMode && !formData.username.trim()) {
      newErrors.username = "Le nom d'utilisateur est requis";
    }

    // Email optionnel mais doit être valide si fourni
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "L'email n'est pas valide";
    }

    // Mot de passe requis en mode création
    if (!isEditMode && !formData.password) {
      newErrors.password = 'Le mot de passe est requis';
    }

    // Validation du mot de passe si fourni
    if (formData.password) {
      if (formData.password.length < 8) {
        newErrors.password = 'Le mot de passe doit contenir au moins 8 caractères';
      }

      if (formData.password !== formData.password_confirm) {
        newErrors.password_confirm = 'Les mots de passe ne correspondent pas';
      }
    }

    // En mode édition, vérifier la confirmation même si mot de passe vide
    if (isEditMode && formData.password_confirm && !formData.password) {
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

    try {
      // Préparer les données à envoyer
      const dataToSubmit = { ...formData };

      // En mode édition, ne pas envoyer username (non modifiable)
      if (isEditMode) {
        delete dataToSubmit.username;
      }

      // Ne pas envoyer le mot de passe s'il est vide en mode édition
      if (isEditMode && !dataToSubmit.password) {
        delete dataToSubmit.password;
        delete dataToSubmit.password_confirm;
      }

      await onSubmit(dataToSubmit);
    } catch (err) {
      // Essayer de parser les erreurs de validation du backend
      try {
        const backendErrors = JSON.parse(err.message);
        setErrors(backendErrors);
      } catch {
        setErrors({ general: err.message });
      }
    } finally {
      setLoading(false);
    }
  };

  // Fermer le modal sur clic en dehors
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal">
        {/* Header */}
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {errors.general && <div className="error-message">{errors.general}</div>}

          <form className="user-form" onSubmit={handleSubmit}>
            {/* Username (non modifiable en mode édition) */}
            <div className="form-group">
              <label htmlFor="username">
                Nom d'utilisateur
                {!isEditMode && <span className="required">*</span>}
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                disabled={isEditMode}
                className={errors.username ? 'error' : ''}
                placeholder="johndoe"
              />
              {errors.username && <div className="form-error">{errors.username}</div>}
              {isEditMode && (
                <div className="form-help">Le nom d'utilisateur ne peut pas être modifié</div>
              )}
            </div>

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
                placeholder="john.doe@example.com"
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

            {/* Rôle */}
            <div className="form-group">
              <label htmlFor="role">
                Rôle
                <span className="required">*</span>
              </label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleChange}
                className={errors.role ? 'error' : ''}
              >
                <option value="lecteur">Lecteur (lecture seule)</option>
                <option value="contributeur">Contributeur (lecture + écriture)</option>
                <option value="admin">Administrateur (tous les droits)</option>
              </select>
              {errors.role && <div className="form-error">{errors.role}</div>}
            </div>

            {/* Statut (seulement en mode édition) */}
            {isEditMode && (
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleChange}
                    style={{ marginRight: '8px' }}
                  />
                  Compte actif
                </label>
                <div className="form-help">
                  Désactiver un compte empêche l'utilisateur de se connecter
                </div>
              </div>
            )}

            {/* Mot de passe */}
            <div className="form-group">
              <label htmlFor="password">
                Mot de passe
                {!isEditMode && <span className="required">*</span>}
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={errors.password ? 'error' : ''}
                placeholder={isEditMode ? 'Laisser vide pour ne pas modifier' : 'Minimum 8 caractères'}
              />
              {errors.password && <div className="form-error">{errors.password}</div>}
              {!errors.password && (
                <div className="form-help">
                  {isEditMode
                    ? 'Laisser vide pour conserver le mot de passe actuel'
                    : 'Minimum 8 caractères'}
                </div>
              )}
            </div>

            {/* Confirmation mot de passe */}
            <div className="form-group">
              <label htmlFor="password_confirm">
                Confirmer le mot de passe
                {!isEditMode && formData.password && <span className="required">*</span>}
              </label>
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
          </form>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Annuler
          </button>
          <button
            type="submit"
            className="btn-submit"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? 'En cours...' : isEditMode ? 'Enregistrer' : 'Créer'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserFormModal;
