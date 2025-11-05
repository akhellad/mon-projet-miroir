import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.contrib.auth import authenticate as django_authenticate
from django.utils import timezone

from .base import AuthBackend
from authentication.models import User, RefreshToken


class JWTAuthBackend(AuthBackend):
    """
    Backend d'authentification JWT pour le POC.

    Configuration dans settings.py:
        AUTH_BACKEND = 'authentication.backends.jwt_backend.JWTAuthBackend'
        JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
        JWT_ACCESS_TOKEN_LIFETIME = timedelta(hours=8)  # Durée journée de travail
        JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)  # Une semaine
        JWT_ALGORITHM = 'HS256'
    """

    def __init__(self):
        self.secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
        self.algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
        self.access_token_lifetime = getattr(
            settings,
            'JWT_ACCESS_TOKEN_LIFETIME',
            timedelta(hours=8)
        )
        self.refresh_token_lifetime = getattr(
            settings,
            'JWT_REFRESH_TOKEN_LIFETIME',
            timedelta(days=7)
        )

    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Authentifie avec Django auth backend (compatible avec migration OIDC).
        """
        user = django_authenticate(username=username, password=password)

        if user is None:
            return False, None, "Identifiants invalides"

        if not user.is_active:
            return False, None, "Compte désactivé"

        user_data = self._serialize_user(user)
        return True, user_data, None

    def generate_tokens(self, user: User) -> Dict[str, str]:
        """
        Génère access token + refresh token JWT.
        """
        now = timezone.now()
        access_exp = now + self.access_token_lifetime
        refresh_exp = now + self.refresh_token_lifetime

        # Access Token (courte durée)
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': access_exp.timestamp(),
            'iat': now.timestamp(),
            'type': 'access'
        }
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)

        # Refresh Token (longue durée)
        refresh_payload = {
            'user_id': user.id,
            'exp': refresh_exp.timestamp(),
            'iat': now.timestamp(),
            'type': 'refresh'
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        # Sauvegarder le refresh token en base (pour révocation)
        RefreshToken.objects.create(
            user=user,
            token=refresh_token,
            expires_at=refresh_exp
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_lifetime.total_seconds())
        }

    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Génère un nouveau access token depuis un refresh token valide.
        """
        try:
            # Vérifier le token en base
            token_obj = RefreshToken.objects.filter(token=refresh_token, revoked=False).first()
            if not token_obj or not token_obj.is_valid:
                return False, None, "Refresh token invalide ou expiré"

            # Décoder le token
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            if payload.get('type') != 'refresh':
                return False, None, "Type de token invalide"

            # Récupérer l'utilisateur
            user = User.objects.get(id=payload['user_id'])
            if not user.is_active:
                return False, None, "Compte désactivé"

            # Générer un nouveau access token
            now = timezone.now()
            access_exp = now + self.access_token_lifetime
            access_payload = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'exp': access_exp.timestamp(),
                'iat': now.timestamp(),
                'type': 'access'
            }
            new_access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)

            return True, {
                'access_token': new_access_token,
                'token_type': 'Bearer',
                'expires_in': int(self.access_token_lifetime.total_seconds())
            }, None

        except jwt.ExpiredSignatureError:
            return False, None, "Refresh token expiré"
        except jwt.InvalidTokenError:
            return False, None, "Refresh token invalide"
        except User.DoesNotExist:
            return False, None, "Utilisateur introuvable"
        except Exception as e:
            return False, None, f"Erreur lors du refresh: {str(e)}"

    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Valide un access token et retourne les données utilisateur.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            if payload.get('type') != 'access':
                return False, None

            return True, payload

        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None

    def revoke_token(self, token: str) -> bool:
        """
        Révoque un refresh token (logout).
        """
        try:
            token_obj = RefreshToken.objects.filter(token=token).first()
            if token_obj:
                token_obj.revoked = True
                token_obj.save()
                return True
            return False
        except Exception:
            return False

    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Récupère l'instance User depuis un access token.
        """
        is_valid, payload = self.validate_token(token)
        if not is_valid or not payload:
            return None

        try:
            user = User.objects.get(id=payload['user_id'], is_active=True)
            return user
        except User.DoesNotExist:
            return None

    def _serialize_user(self, user: User) -> Dict:
        """
        Sérialise un utilisateur en dictionnaire.
        """
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'role_display': user.get_role_display(),
            'is_admin': user.is_admin,
            'is_contributeur': user.is_contributeur,
            'must_change_password': user.must_change_password,
        }
