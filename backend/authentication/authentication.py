from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .services.auth_service import AuthService


class JWTAuthentication(BaseAuthentication):
    """
    Classe d'authentification JWT pour Django REST Framework.

    Cette classe permet à DRF de gérer automatiquement l'authentification JWT
    et de désactiver le CSRF pour les endpoints API.
    """
    keyword = 'Bearer'

    def authenticate(self, request):
        """
        Authentifie la requête en extrayant le token JWT du header Authorization.

        Returns:
            tuple: (user, token) si authentifié, None sinon
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            return None

        try:
            keyword, token = auth_header.split()
            if keyword.lower() != self.keyword.lower():
                return None
        except ValueError:
            return None

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        """
        Valide le token et retourne l'utilisateur.
        """
        user = AuthService.get_user_from_token(token)

        if user is None:
            raise exceptions.AuthenticationFailed('Token invalide')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('Compte désactivé')

        return (user, token)

    def authenticate_header(self, request):
        """
        Retourne le header WWW-Authenticate pour les erreurs 401.
        """
        return self.keyword
