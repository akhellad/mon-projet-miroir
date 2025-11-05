import { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './PasswordChangePrompt.css';
import './UserProfile.css';

/**
 * Page de changement obligatoire de mot de passe
 *
 * Affichée lorsque must_change_password=true
 * L'utilisateur ne peut pas accéder à l'application tant qu'il n'a pas changé son mot de passe
 */
const ForcePasswordChange = ({ onPasswordChanged }) => {
  const [formData, setFormData] = useState({
    password: '',
    password_confirm: ''
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
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

    // Mot de passe requis
    if (!formData.password) {
      newErrors.password = 'Le mot de passe est requis';
    } else if (formData.password.length < 20) {
      newErrors.password = 'Le mot de passe doit contenir au moins 20 caractères';
    }

    // Confirmation requise
    if (!formData.password_confirm) {
      newErrors.password_confirm = 'Veuillez confirmer le mot de passe';
    } else if (formData.password !== formData.password_confirm) {
      newErrors.password_confirm = 'Les mots de passe ne correspondent pas';
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

    try {
      // Mettre à jour le mot de passe
      await axios.patch(`${API_BASE_URL}/api/auth/profile/`, formData);

      // Notifier le parent que le mot de passe a été changé
      onPasswordChanged();
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
    <div className="password-prompt-container">
      <div className="password-prompt-card">
        <div className="prompt-header">
          <h2>Changement de mot de passe</h2>
          <p className="prompt-subtitle">
            Définissez votre nouveau mot de passe personnel
          </p>
        </div>

        <div className="prompt-content">
          <div className="info-banner" style={{ background: '#fef3c7', borderColor: '#fbbf24' }}>
            <div className="info-banner-title" style={{ color: '#92400e' }}>Mot de passe temporaire</div>
            <p className="info-banner-text" style={{ color: '#92400e' }}>
              Un mot de passe temporaire vous a été attribué par l'administrateur.
              Pour accéder à l'application, vous devez définir un nouveau mot de passe personnel.
            </p>
          </div>

          {/* Messages */}
          {error && <div className="error-message">{error}</div>}

          <form className="profile-form" onSubmit={handleSubmit}>
            {/* Nouveau mot de passe */}
            <div className="form-group">
              <label htmlFor="password">
                Nouveau mot de passe
                <span className="required">*</span>
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={errors.password ? 'error' : ''}
                placeholder="Minimum 20 caractères"
                autoFocus
              />
              {errors.password && <div className="form-error">{errors.password}</div>}
            </div>

            {/* Confirmation */}
            <div className="form-group">
              <label htmlFor="password_confirm">
                Confirmer le nouveau mot de passe
                <span className="required">*</span>
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

            {/* Critères de sécurité */}
            <div className="password-info-box">
              <strong>Critères de sécurité</strong>
              <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', fontSize: '13px', lineHeight: '1.8' }}>
                <li>Au moins 20 caractères</li>
                <li>Au moins une lettre majuscule (A-Z)</li>
                <li>Au moins une lettre minuscule (a-z)</li>
                <li>Au moins un chiffre (0-9)</li>
                <li>Au moins un caractère spécial (!@#$%...)</li>
              </ul>
            </div>

            {/* Boutons */}
            <div className="form-actions">
              <button type="submit" className="btn-submit" disabled={loading}>
                {loading ? 'Enregistrement...' : 'Valider et accéder à l\'application'}
              </button>
            </div>
          </form>

          <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '13px', color: '#64748b' }}>
            <p>
              Vous ne pouvez pas changer votre mot de passe ?<br />
              Contactez votre administrateur.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForcePasswordChange;
