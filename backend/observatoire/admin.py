"""
Configuration de l'interface d'administration Django pour l'Observatoire SDAEP.

Enregistre les modèles de l'application avec leurs interfaces d'administration personnalisées.
"""

from django.contrib.gis import admin
from .models import Layer, Feature


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les couches SIG.

    Permet de gérer les couches de données géographiques avec visualisation
    du nombre d'entités et filtres par type de géométrie.
    """
    list_display = ['name', 'geometry_type', 'feature_count', 'visible', 'created_at']
    list_filter = ['geometry_type', 'visible']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def feature_count(self, obj):
        """Retourne le nombre d'entités associées à la couche."""
        return obj.features.count()
    feature_count.short_description = 'Nombre d\'entités'


@admin.register(Feature)
class FeatureAdmin(admin.GISModelAdmin):
    """
    Interface d'administration pour les entités géographiques.

    Utilise GISModelAdmin pour permettre la visualisation et l'édition
    des géométries directement dans l'interface d'administration.
    """
    list_display = ['id', 'layer', 'get_identifier', 'created_at']
    list_filter = ['layer']
    search_fields = ['properties']

    def get_identifier(self, obj):
        """
        Extrait l'identifiant de l'entité depuis ses propriétés JSON.

        L'identifiant utilisé dépend du champ identifier_field défini dans la couche.
        """
        return obj.properties.get(obj.layer.identifier_field, 'N/A')
    get_identifier.short_description = 'Identifiant'
