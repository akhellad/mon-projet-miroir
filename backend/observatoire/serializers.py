"""
Serializers pour l'API REST de l'Observatoire SDAEP.

Convertit les modèles Django en représentations JSON et GeoJSON pour le frontend.
"""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Layer, Feature


class LayerSerializer(serializers.ModelSerializer):
    """
    Serializer pour les couches géographiques.

    Inclut le décompte des entités associées à la couche.
    """
    feature_count = serializers.SerializerMethodField()

    class Meta:
        model = Layer
        fields = [
            'id', 'name', 'description', 'geometry_type', 'identifier_field',
            'style_color', 'style_weight', 'style_opacity', 'style_fill_opacity',
            'source_file', 'srid', 'visible', 'created_at', 'updated_at', 'feature_count'
        ]

    def get_feature_count(self, obj):
        """Retourne le nombre d'entités dans la couche."""
        return obj.features.count()


class FeatureSerializer(GeoFeatureModelSerializer):
    """
    Serializer pour les entités géographiques au format GeoJSON.

    Transforme automatiquement les géométries de Lambert 93 (EPSG:2154)
    vers WGS84 (EPSG:4326) pour compatibilité avec les librairies cartographiques web.
    """
    class Meta:
        model = Feature
        geo_field = "geom"
        fields = ['id']
        auto_bbox = False

    def to_representation(self, instance):
        """
        Personnalise la représentation GeoJSON.

        Transforme le SRID et injecte les propriétés JSON dans l'objet GeoJSON.
        """
        # Transformation Lambert 93 -> WGS84 si nécessaire
        if instance.geom.srid != 4326:
            instance.geom.transform(4326)

        representation = super().to_representation(instance)

        # Injection des propriétés JSON dans l'objet GeoJSON
        representation['properties'] = instance.properties

        return representation