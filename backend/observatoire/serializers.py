"""
Serializers pour l'API REST de l'Observatoire SDAEP.

Convertit les modèles Django en représentations JSON et GeoJSON pour le frontend.
"""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.core.exceptions import ObjectDoesNotExist
from .models import (
    Layer, Feature, Arrondissement, Canton, Commune,
    UGE, UDI, Captage
)


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
            'source_file', 'srid', 'visible', 'order', 'created_at', 'updated_at', 'feature_count'
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

        Transforme le SRID et sérialise automatiquement tous les champs
        du modèle métier associé (Commune, Captage, etc.).
        """
        # Transformation Lambert 93 -> WGS84 si nécessaire
        if instance.geom.srid != 4326:
            instance.geom.transform(4326)

        representation = super().to_representation(instance)

        # Récupération automatique du modèle métier associé
        properties = {'id': instance.id}

        # Liste des relations OneToOne possibles
        related_models = ['commune', 'captage', 'uge', 'udi', 'canton', 'arrondissement']

        for related_name in related_models:
            try:
                # Essayer de récupérer l'objet associé
                related_obj = getattr(instance, related_name)

                # Sérialisation automatique de tous les champs du modèle
                for field in related_obj._meta.get_fields():
                    # Ignorer les champs spéciaux et les relations inversées
                    if field.name in ['id', 'feature', 'created_at', 'updated_at']:
                        continue

                    # Gestion spéciale des ManyToMany (ex: UDI pour communes)
                    if field.many_to_many:
                        if field.name == 'udis':
                            # Récupérer la liste des UDI associées
                            udis_list = []
                            for udi in getattr(related_obj, field.name).all():
                                udis_list.append({
                                    'id': udi.id,
                                    'code_ins_udi': udi.code_ins_udi,
                                    'nom_ins_udi': udi.nom_ins_udi,
                                    'type_usage_direct': udi.type_usage_direct,
                                    'type_etat_activite_ins': udi.type_etat_activite_ins,
                                    'nom_quartier': udi.nom_quartier,
                                })
                            properties[field.name] = udis_list
                        continue

                    # Ignorer les relations inversées (ManyToOne)
                    if field.one_to_many:
                        continue

                    try:
                        value = getattr(related_obj, field.name)

                        # Ignorer les valeurs None
                        if value is None:
                            properties[field.name] = None
                            continue

                        # Conversion des types spéciaux
                        if hasattr(value, 'isoformat'):  # Date/DateTime
                            value = value.isoformat()
                        elif hasattr(value, '__float__'):  # Decimal
                            value = float(value)
                        elif field.many_to_one or field.one_to_one:  # ForeignKey ou OneToOne
                            # Convertir l'objet en string via __str__
                            value = str(value)
                        elif isinstance(value, bool):  # Boolean
                            value = value
                        elif isinstance(value, (int, float, str)):  # Types de base
                            value = value
                        else:
                            # Pour tout autre type, convertir en string
                            value = str(value)

                        properties[field.name] = value
                    except Exception as e:
                        # En cas d'erreur, ignorer ce champ
                        continue

                break  # On a trouvé le modèle associé, pas besoin de continuer
            except (AttributeError, ObjectDoesNotExist):
                # Cette relation n'existe pas pour cette instance, continuer
                continue

        representation['properties'] = properties

        return representation