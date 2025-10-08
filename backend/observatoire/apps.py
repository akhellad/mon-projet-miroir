"""
Configuration de l'application Observatoire.

Cette application gère les données géographiques du SDAEP de l'Ardèche.
"""

from django.apps import AppConfig


class ObservatoireConfig(AppConfig):
    """Configuration de l'application principale de l'observatoire."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'observatoire'
    verbose_name = 'Observatoire SDAEP'
