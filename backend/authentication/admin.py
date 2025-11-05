from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RefreshToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Interface d'administration pour les utilisateurs.
    """
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Rôle et Permissions', {
            'fields': ('role',)
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Rôle', {
            'fields': ('role',)
        }),
    )


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les refresh tokens.
    """
    list_display = ['user', 'created_at', 'expires_at', 'revoked']
    list_filter = ['revoked', 'created_at', 'expires_at']
    search_fields = ['user__username', 'token']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        # Les tokens ne doivent être créés que via l'API
        return False
