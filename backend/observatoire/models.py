"""
Modèles de données pour l'Observatoire SDAEP.

Définit la structure de stockage des couches géographiques et de leurs entités
dans PostgreSQL/PostGIS.
"""

from django.contrib.gis.db import models


class Layer(models.Model):
    """
    Modèle représentant une couche géographique (layer SIG).

    Une couche regroupe des entités de même nature (communes, captages, conduites, etc.)
    avec des métadonnées de style et de configuration pour l'affichage cartographique.
    """
    GEOMETRY_TYPES = [
        ('Point', 'Point'),
        ('LineString', 'Ligne'),
        ('Polygon', 'Polygone'),
        ('MultiPoint', 'Multi-points'),
        ('MultiLineString', 'Multi-lignes'),
        ('MultiPolygon', 'Multi-polygones'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom de la couche")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    geometry_type = models.CharField(max_length=50, choices=GEOMETRY_TYPES, verbose_name="Type de géométrie")
    identifier_field = models.CharField(max_length=100, default='id', verbose_name="Champ identifiant")

    # Configuration de style pour l'affichage cartographique
    style_color = models.CharField(max_length=7, default='#3388ff', verbose_name="Couleur")
    style_weight = models.IntegerField(default=2, verbose_name="Épaisseur du trait")
    style_opacity = models.FloatField(default=0.8, verbose_name="Opacité")
    style_fill_opacity = models.FloatField(default=0.2, verbose_name="Opacité du remplissage")

    # Métadonnées de source et référencement spatial
    source_file = models.CharField(max_length=500, blank=True, null=True, verbose_name="Fichier source")
    srid = models.IntegerField(default=2154, verbose_name="SRID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    # Contrôle de visibilité
    visible = models.BooleanField(default=True, verbose_name="Visible par défaut")

    class Meta:
        db_table = 'layers'
        ordering = ['name']

    def __str__(self):
        return self.name


class Feature(models.Model):
    """
    Modèle représentant une entité géographique.

    Chaque feature appartient à une couche et contient une géométrie PostGIS
    ainsi que des propriétés alphanumériques stockées en JSON pour une flexibilité maximale.
    """
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name='features', verbose_name="Couche")

    # Géométrie PostGIS (type générique supportant tous les types de géométries)
    geom = models.GeometryField(srid=2154, verbose_name="Géométrie")

    # Propriétés alphanumériques en JSON (schéma flexible)
    properties = models.JSONField(default=dict, verbose_name="Propriétés")

    # Métadonnées de suivi
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'features'
        indexes = [
            models.Index(fields=['layer']),
        ]

    def __str__(self):
        identifier = self.properties.get(self.layer.identifier_field, 'N/A')
        return f"{self.layer.name} - {identifier}"