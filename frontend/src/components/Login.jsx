import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Login.css';

/**
 * Composant de connexion
 *
 * Interface simple et moderne pour l'authentification.
 */
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  // Rediriger vers la page d'accueil si déjà connecté (au chargement initial)
  useEffect(() => {
    if (!authLoading && isAuthenticated && !loading) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(username, password);

      if (result.success) {
        // Rediriger vers la page principale
        navigate('/');
      } else {
        setError(result.error || 'Erreur de connexion');
      }
    } catch (err) {
      setError('Une erreur est survenue lors de la connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <h1>SDAEP Observatoire</h1>
          <p>Connexion à la plateforme</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Nom d'utilisateur</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Entrez votre nom d'utilisateur"
              required
              autoFocus
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Entrez votre mot de passe"
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <div className="login-footer">
          <p>Contactez votre administrateur pour obtenir un compte.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
