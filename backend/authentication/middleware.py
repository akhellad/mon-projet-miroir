from django.utils.functional import SimpleLazyObject
from rest_framework.authentication import get_authorization_header

from .services.auth_service import AuthService


def get_user_from_token(request):
    """
    Récupère l'utilisateur depuis le token JWT dans le header Authorization.
    """
    from django.contrib.auth.models import AnonymousUser

    auth_header = get_authorization_header(request).decode('utf-8')

    if not auth_header or not auth_header.startswith('Bearer '):
        return AnonymousUser()

    token = auth_header.replace('Bearer ', '')
    user = AuthService.get_user_from_token(token)
    return user if user else AnonymousUser()


class JWTAuthenticationMiddleware:
    """
    Middleware Django pour authentifier automatiquement les utilisateurs
    via JWT token.

    Ce middleware extrait le token du header Authorization et injecte
    l'utilisateur dans request.user.

    Compatible avec Django REST Framework et permet d'utiliser
    IsAuthenticated, permissions, etc.

    Configuration dans settings.py:
        MIDDLEWARE = [
            ...
            'authentication.middleware.JWTAuthenticationMiddleware',
            ...
        ]
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Injecter l'utilisateur de manière lazy (évite les requêtes DB inutiles)
        request.user = SimpleLazyObject(lambda: get_user_from_token(request))

        response = self.get_response(request)
        return response
