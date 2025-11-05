from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple


class AuthBackend(ABC):
    """
    Interface abstraite pour les backends d'authentification.

    Cette classe définit le contrat que tous les backends d'auth
    doivent respecter, permettant de basculer facilement entre JWT,
    OpenID Connect, ou tout autre système.

    Usage:
        # Dans settings.py
        AUTH_BACKEND = 'authentication.backends.jwt_backend.JWTAuthBackend'
        # ou
        AUTH_BACKEND = 'authentication.backends.oidc_backend.OIDCAuthBackend'
    """

    @abstractmethod
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Authentifie un utilisateur avec ses credentials.

        Args:
            username: Nom d'utilisateur ou email
            password: Mot de passe

        Returns:
            Tuple (success, user_data, error_message)
            - success: True si l'authentification a réussi
            - user_data: Dict contenant les données utilisateur si succès
            - error_message: Message d'erreur si échec

        Example:
            success, user_data, error = backend.authenticate('admin', 'password123')
            if success:
                print(f"Connecté en tant que {user_data['username']}")
        """
        pass

    @abstractmethod
    def generate_tokens(self, user) -> Dict[str, str]:
        """
        Génère les tokens d'authentification pour un utilisateur.

        Args:
            user: Instance du modèle User

        Returns:
            Dict contenant les tokens:
            {
                'access_token': 'eyJ...',
                'refresh_token': 'eyJ...',
                'token_type': 'Bearer',
                'expires_in': 28800
            }
        """
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Génère un nouveau access token à partir d'un refresh token.

        Args:
            refresh_token: Le refresh token valide

        Returns:
            Tuple (success, token_data, error_message)
        """
        pass

    @abstractmethod
    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Valide un token et retourne les données utilisateur.

        Args:
            token: Le token à valider

        Returns:
            Tuple (is_valid, user_data)
        """
        pass

    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """
        Révoque un token (logout).

        Args:
            token: Le token à révoquer

        Returns:
            True si la révocation a réussi
        """
        pass

    @abstractmethod
    def get_user_from_token(self, token: str):
        """
        Récupère l'instance User depuis un token.

        Args:
            token: Le token d'accès

        Returns:
            Instance User ou None
        """
        pass
