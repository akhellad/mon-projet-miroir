from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    """
    Définition des rôles utilisateurs.

    - ADMIN: Accès complet (gestion utilisateurs, upload, export, delete)
    - CONTRIBUTEUR: Peut uploader et modifier des données
    - LECTEUR: Lecture seule
    """
    ADMIN = 'admin', 'Administrateur'
    CONTRIBUTEUR = 'contributeur', 'Contributeur'
    LECTEUR = 'lecteur', 'Lecteur'


class User(AbstractUser):
    """
    Modèle User étendu avec système de rôles.

    Architecture flexible permettant de basculer facilement vers
    OpenID Connect tout en conservant la logique de permissions.
    """
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.LECTEUR,
        verbose_name="Rôle",
        help_text="Définit les permissions de l'utilisateur dans le système"
    )

    must_change_password = models.BooleanField(
        default=False,
        verbose_name="Doit changer le mot de passe",
        help_text="Oblige l'utilisateur à changer son mot de passe à la prochaine connexion"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur."""
        return self.role == UserRole.ADMIN

    @property
    def is_contributeur(self):
        """Vérifie si l'utilisateur est contributeur ou admin."""
        return self.role in [UserRole.ADMIN, UserRole.CONTRIBUTEUR]

    @property
    def is_lecteur(self):
        """Vérifie si l'utilisateur a au moins un accès en lecture."""
        return self.role in [UserRole.ADMIN, UserRole.CONTRIBUTEUR, UserRole.LECTEUR]

    def has_permission(self, permission):
        """
        Vérifie si l'utilisateur a une permission spécifique.

        Architecture extensible pour permissions granulaires futures.
        """
        permission_map = {
            'can_read': [UserRole.ADMIN, UserRole.CONTRIBUTEUR, UserRole.LECTEUR],
            'can_upload': [UserRole.ADMIN, UserRole.CONTRIBUTEUR],
            'can_edit': [UserRole.ADMIN, UserRole.CONTRIBUTEUR],
            'can_delete': [UserRole.ADMIN],
            'can_export': [UserRole.ADMIN, UserRole.CONTRIBUTEUR],
            'can_manage_users': [UserRole.ADMIN],
        }

        return self.role in permission_map.get(permission, [])


class RefreshToken(models.Model):
    """
    Gestion des refresh tokens pour le système JWT.

    Permet d'invalider les sessions et de gérer la sécurité.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=500, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Refresh Token"
        verbose_name_plural = "Refresh Tokens"
        ordering = ['-created_at']

    def __str__(self):
        return f"Token for {self.user.username} - {'Revoked' if self.revoked else 'Active'}"

    @property
    def is_valid(self):
        """Vérifie si le token est toujours valide."""
        from django.utils import timezone
        return not self.revoked and self.expires_at > timezone.now()
