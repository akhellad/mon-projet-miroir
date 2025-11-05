import { useState } from 'react';
import './UserManagement.css';

/**
 * Modal de création d'utilisateur avec génération automatique de mot de passe
 *
 * Props:
 * - onSubmit: Callback pour soumettre le formulaire
 * - onClose: Callback pour fermer le modal
 */
const UserCreateModal = ({ onSubmit, onClose }) => {
  // État du formulaire
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'lecteur'
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [generatedPassword, setGeneratedPassword] = useState(null);
  const [passwordCopied, setPasswordCopied] = useState(false);

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

    // Username requis
    if (!formData.username.trim()) {
      newErrors.username = "Le nom d'utilisateur est requis";
    }

    // Email optionnel mais doit être valide si fourni
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "L'email n'est pas valide";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Copier le mot de passe dans le presse-papier
  const copyPassword = () => {
    if (generatedPassword) {
      navigator.clipboard.writeText(generatedPassword);
      setPasswordCopied(true);
      setTimeout(() => setPasswordCopied(false), 2000);
    }
  };

  // Soumettre le formulaire
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setLoading(true);

    try {
      // Le mot de passe sera généré automatiquement côté backend
      const result = await onSubmit(formData);

      // Si la création réussit, le backend retourne le mot de passe généré
      if (result && result.generated_password) {
        setGeneratedPassword(result.generated_password);
      }
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
          <h3>Créer un utilisateur</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {errors.general && <div className="error-message">{errors.general}</div>}

          {!generatedPassword ? (
            // Formulaire de création
            <form className="user-form" onSubmit={handleSubmit}>
              {/* Username */}
              <div className="form-group">
                <label htmlFor="username">
                  Nom d'utilisateur
                  <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  className={errors.username ? 'error' : ''}
                  placeholder="johndoe"
                />
                {errors.username && <div className="form-error">{errors.username}</div>}
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

              {/* Info mot de passe */}
              <div className="password-info-box">
                <strong>Mot de passe automatique</strong>
                <p>
                  Un mot de passe sécurisé de 20 caractères sera généré automatiquement.
                  L'utilisateur devra le changer lors de sa première connexion.
                </p>
              </div>
            </form>
          ) : (
            // Affichage du mot de passe généré
            <div className="password-generated-container">
              <h4>Utilisateur créé avec succès</h4>
              <p>
                L'utilisateur <strong>{formData.username}</strong> a été créé.
                Voici son mot de passe temporaire :
              </p>

              <div className="generated-password-box">
                <code className="generated-password">{generatedPassword}</code>
                <button
                  type="button"
                  className="btn-copy"
                  onClick={copyPassword}
                  title="Copier le mot de passe"
                >
                  {passwordCopied ? 'Copié' : 'Copier'}
                </button>
              </div>

              <div className="password-warning-box">
                <strong>Important</strong>
                <ul>
                  <li>Copiez ce mot de passe immédiatement</li>
                  <li>Communiquez-le à l'utilisateur de manière sécurisée</li>
                  <li>Ce mot de passe ne sera plus affiché après la fermeture</li>
                  <li>L'utilisateur devra le changer à sa première connexion</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          {!generatedPassword ? (
            <>
              <button type="button" className="btn-cancel" onClick={onClose}>
                Annuler
              </button>
              <button
                type="submit"
                className="btn-submit"
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? 'Création...' : 'Créer l\'utilisateur'}
              </button>
            </>
          ) : (
            <button type="button" className="btn-submit" onClick={onClose}>
              Fermer
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserCreateModal;
