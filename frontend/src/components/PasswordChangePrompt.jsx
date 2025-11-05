import { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './PasswordChangePrompt.css';

/**
 * Modal de confirmation pour le changement de mot de passe
 *
 * Affichée lors de la première connexion avec un mot de passe généré.
 * L'utilisateur peut choisir de :
 * - Changer son mot de passe → redirigé vers ForcePasswordChange
 * - Garder le mot de passe généré → marque must_change_password=false
 */
const PasswordChangePrompt = ({ user, onChangePassword, onKeepPassword }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Gérer le choix "Garder le mot de passe"
  const handleKeepPassword = async () => {
    setLoading(true);
    setError(null);

    try {
      // Appeler l'API pour marquer que l'utilisateur accepte son mot de passe
      await axios.patch(`${API_BASE_URL}/api/auth/profile/accept-password/`);

      // Notifier le parent que le mot de passe a été accepté
      onKeepPassword();
    } catch (err) {
      setError(err.response?.data?.error || 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="password-prompt-container">
      <div className="password-prompt-card">
        <div className="prompt-header">
          <h2>Bienvenue {user?.first_name || user?.username}</h2>
          <p className="prompt-subtitle">
            Configuration initiale de votre compte
          </p>
        </div>

        <div className="prompt-content">
          <div className="info-banner">
            <div className="info-banner-title">Mot de passe temporaire</div>
            <p className="info-banner-text">
              Un mot de passe sécurisé de 20 caractères a été généré automatiquement
              pour votre compte par l'administrateur.
            </p>
          </div>

          <h3 className="prompt-question">Que souhaitez-vous faire ?</h3>

          {error && <div className="error-message">{error}</div>}

          <div className="options-container">
            {/* Option 1: Changer le mot de passe */}
            <div className="option-card option-primary">
              <div className="option-header">
                <h4>Définir mon propre mot de passe</h4>
              </div>
              <p className="option-description">
                Choisissez un mot de passe personnel qui répond aux critères de sécurité
                (minimum 20 caractères avec majuscules, minuscules, chiffres et caractères spéciaux).
              </p>
              <button
                type="button"
                className="btn-option btn-primary"
                onClick={onChangePassword}
                disabled={loading}
              >
                Définir un nouveau mot de passe
              </button>
            </div>

            {/* Option 2: Garder le mot de passe */}
            <div className="option-card option-secondary">
              <div className="option-header">
                <h4>Conserver le mot de passe généré</h4>
              </div>
              <p className="option-description">
                Le mot de passe généré automatiquement respecte tous les critères de sécurité.
                Vous pouvez le conserver et commencer à utiliser l'application immédiatement.
              </p>
              <button
                type="button"
                className="btn-option btn-secondary"
                onClick={handleKeepPassword}
                disabled={loading}
              >
                {loading ? 'Validation en cours...' : 'Conserver ce mot de passe'}
              </button>
            </div>
          </div>

          {/* Note de sécurité */}
          <div className="security-note">
            <strong>Important :</strong>
            <span>
              Conservez votre mot de passe dans un endroit sûr. Vous pourrez le modifier
              ultérieurement depuis votre profil utilisateur.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PasswordChangePrompt;
