from django.conf import settings
from django.utils.module_loading import import_string


class AuthService:
    """
    Service unifié d'authentification.

    Permet de basculer entre différents backends (JWT, OIDC, etc.)
    via la configuration Django settings.AUTH_BACKEND.

    Usage:
        auth_service = AuthService()
        success, user_data, error = auth_service.login('admin', 'password')
    """

    _backend = None

    @classmethod
    def get_backend(cls):
        """
        Charge le backend d'authentification configuré.

        Par défaut : JWTAuthBackend
        """
        if cls._backend is None:
            backend_path = getattr(
                settings,
                'AUTH_BACKEND',
                'authentication.backends.jwt_backend.JWTAuthBackend'
            )
            backend_class = import_string(backend_path)
            cls._backend = backend_class()
        return cls._backend

    @classmethod
    def login(cls, username: str, password: str):
        """
        Authentifie un utilisateur et génère les tokens.
        """
        backend = cls.get_backend()
        success, user_data, error = backend.authenticate(username, password)

        if not success:
            return False, None, error

        # Récupérer l'utilisateur pour générer les tokens
        from authentication.models import User
        user = User.objects.get(username=username)
        tokens = backend.generate_tokens(user)

        return True, {
            'user': user_data,
            'tokens': tokens
        }, None

    @classmethod
    def refresh(cls, refresh_token: str):
        """
        Rafraîchit l'access token.
        """
        backend = cls.get_backend()
        return backend.refresh_access_token(refresh_token)

    @classmethod
    def logout(cls, refresh_token: str):
        """
        Déconnecte l'utilisateur (révoque le refresh token).
        """
        backend = cls.get_backend()
        return backend.revoke_token(refresh_token)

    @classmethod
    def validate_token(cls, token: str):
        """
        Valide un access token.
        """
        backend = cls.get_backend()
        return backend.validate_token(token)

    @classmethod
    def get_user_from_token(cls, token: str):
        """
        Récupère l'utilisateur depuis un token.
        """
        backend = cls.get_backend()
        return backend.get_user_from_token(token)
