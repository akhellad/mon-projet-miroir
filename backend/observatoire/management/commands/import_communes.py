"""
Commande d'import des communes de l'Ardèche.

Cette commande récupère les données géographiques des communes du département 07
depuis l'API geo.api.gouv.fr et les stocke dans la base de données PostgreSQL/PostGIS.

Usage:
    python manage.py import_communes [--force]

Options:
    --force : Supprime la couche existante avant l'import
"""

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from observatoire.models import Layer, Feature, Commune
import requests
import json


class Command(BaseCommand):
    help = 'Importe les communes de l\'Ardèche (département 07) depuis l\'API geo.api.gouv.fr'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Supprimer la couche Communes existante avant l\'import',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Début de l\'import des communes de l\'Ardèche...'))

        # Vérification de l'existence d'une couche Communes
        existing_layer = Layer.objects.filter(name='Communes').first()

        if existing_layer:
            if options['force']:
                self.stdout.write(self.style.WARNING(
                    f'Suppression de la couche existante "{existing_layer.name}"...'
                ))
                existing_layer.delete()
            else:
                self.stdout.write(self.style.ERROR(
                    'Une couche "Communes" existe déjà. Utilisez --force pour la remplacer.'
                ))
                return

        # Création de la couche Communes avec configuration de style
        layer = Layer.objects.create(
            name='Communes',
            description='Communes de l\'Ardèche (département 07)',
            geometry_type='MultiPolygon',
            identifier_field='code_insee',
            style_color='#FFA500',
            style_weight=2,
            style_opacity=0.8,
            style_fill_opacity=0.1,
            source_file='geo.api.gouv.fr',
            srid=2154,  # Lambert 93
            visible=True
        )

        self.stdout.write(self.style.SUCCESS(f'Couche "{layer.name}" créée'))

        # Configuration de l'API geo.api.gouv.fr
        url = 'https://geo.api.gouv.fr/communes'
        params = {
            'codeDepartement': '07',
            'fields': 'nom,code,codesPostaux,population,contour',
            'format': 'geojson',
            'geometry': 'contour'
        }

        try:
            self.stdout.write('Récupération des données depuis geo.api.gouv.fr...')
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            features = data.get('features', [])

            self.stdout.write(self.style.SUCCESS(f'{len(features)} communes trouvées'))

            created_count = 0

            for feature in features:
                props = feature['properties']
                geometry = feature['geometry']

                # Conversion de la géométrie GeoJSON en objet GeoDjango
                # L'API retourne des coordonnées WGS84 (EPSG:4326)
                # Transformation nécessaire vers Lambert 93 (EPSG:2154)
                geom = GEOSGeometry(json.dumps(geometry), srid=4326)
                geom.transform(2154)

                # Normalisation en MultiPolygon si nécessaire
                if geom.geom_type == 'Polygon':
                    geom = MultiPolygon(geom)

                code_insee = props['code']
                nom = props['nom']
                population = props.get('population')
                code_postals = props.get('codesPostaux', [])

                # Enregistrement de la feature en base
                feature_obj = Feature.objects.create(
                    layer=layer,
                    geom=geom
                )

                # Création de la commune avec tous les champs disponibles
                Commune.objects.create(
                    code_insee=code_insee,
                    nom=nom,
                    feature=feature_obj,
                    superficie_km2=geom.area / 1_000_000,
                    population=population,
                    code_postal_commune=code_postals[0] if code_postals else None
                )

                created_count += 1
                self.stdout.write(f'  Importée: {nom} ({code_insee}) - {population} hab.')

            self.stdout.write(self.style.SUCCESS(f'\nImport terminé avec succès'))
            self.stdout.write(self.style.SUCCESS(f'{created_count} communes importées'))
            self.stdout.write(self.style.SUCCESS(f'Couche "{layer.name}" prête à être affichée'))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de la récupération des données: {e}'))
            layer.delete()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur inattendue: {e}'))
            layer.delete()
            raise
