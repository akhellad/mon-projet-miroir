from rest_framework.permissions import BasePermission


class IsAuthenticated(BasePermission):
    """
    Permission de base : utilisateur authentifié.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsAdmin(BasePermission):
    """
    Permission : utilisateur avec rôle Admin uniquement.

    Usage dans les views:
        @permission_classes([IsAdmin])
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsContributeurOrAdmin(BasePermission):
    """
    Permission : utilisateur avec rôle Contributeur ou Admin.

    Utilisé pour les opérations d'écriture (upload, edit, delete).
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_contributeur
        )


class IsLecteurOrAbove(BasePermission):
    """
    Permission : utilisateur avec rôle Lecteur, Contributeur ou Admin.

    Utilisé pour les opérations de lecture (GET).
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_lecteur
        )


class RoleBasedPermission(BasePermission):
    """
    Permission dynamique basée sur les rôles et les méthodes HTTP.

    Configuration dans les ViewSets:
        permission_classes = [RoleBasedPermission]
        role_permissions = {
            'GET': ['lecteur', 'contributeur', 'admin'],
            'POST': ['contributeur', 'admin'],
            'PATCH': ['contributeur', 'admin'],
            'DELETE': ['admin']
        }

    Par défaut (si non configuré):
        - GET: Lecteur, Contributeur, Admin
        - POST/PATCH/PUT: Contributeur, Admin
        - DELETE: Admin uniquement
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Récupérer la configuration de permissions de la vue
        role_permissions = getattr(view, 'role_permissions', None)

        if role_permissions is None:
            # Permissions par défaut
            role_permissions = {
                'GET': ['lecteur', 'contributeur', 'admin'],
                'POST': ['contributeur', 'admin'],
                'PATCH': ['contributeur', 'admin'],
                'PUT': ['contributeur', 'admin'],
                'DELETE': ['admin']
            }

        # Vérifier les permissions pour la méthode HTTP
        allowed_roles = role_permissions.get(request.method, [])
        return request.user.role in allowed_roles


class CanUploadShapefile(BasePermission):
    """
    Permission spécifique : upload de shapefile.

    Peut être étendue pour des règles plus complexes (quotas, etc.).
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_permission('can_upload')
        )


class CanExportData(BasePermission):
    """
    Permission spécifique : export de données.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_permission('can_export')
        )


class CanManageUsers(BasePermission):
    """
    Permission spécifique : gestion des utilisateurs.

    Réservée aux admins (création/modification/suppression de comptes).
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_permission('can_manage_users')
        )
