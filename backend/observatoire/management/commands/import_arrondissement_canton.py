"""
Commande d'import des cantons et arrondissements de l'Ardèche depuis des fichiers GeoJSON.

Usage:
    python manage.py import_cantons_arrondissements [--force] [--canton-file PATH] [--arrondissement-file PATH]

Options:
    --force : Supprime les couches existantes avant l'import
    --canton-file : Chemin vers le fichier GeoJSON des cantons
    --arrondissement-file : Chemin vers le fichier GeoJSON des arrondissements
"""

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from observatoire.models import Layer, Feature, Canton, Arrondissement
import json
import os


class Command(BaseCommand):
    help = 'Importe les cantons et arrondissements de l\'Ardèche depuis des fichiers GeoJSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Supprimer les couches existantes avant l\'import',
        )
        parser.add_argument(
            '--canton-file',
            type=str,
            required=True,
            help='Chemin vers le fichier GeoJSON des cantons'
        )
        parser.add_argument(
            '--arrondissement-file',
            type=str,
            required=True,
            help='Chemin vers le fichier GeoJSON des arrondissements'
        )

    def handle(self, *args, **options):
        force = options['force']
        canton_file = options['canton_file']
        arrondissement_file = options['arrondissement_file']

        self.stdout.write(self.style.SUCCESS('Début de l\'import des arrondissements et cantons...'))

        # --- ARRONDISSEMENTS ---
        existing_layer = Layer.objects.filter(name='Arrondissements').first()
        if existing_layer:
            if force:
                self.stdout.write(self.style.WARNING(f'Suppression de la couche existante "{existing_layer.name}"...'))
                existing_layer.delete()
            else:
                self.stdout.write(self.style.ERROR('Une couche "Arrondissements" existe déjà. Utilisez --force.'))
                return

        layer_arr = Layer.objects.create(
            name='Arrondissements',
            description='Arrondissements de l\'Ardèche',
            geometry_type='MultiPolygon',
            identifier_field='code_arrondissement',
            style_color='#00cc66',
            style_weight=2,
            style_opacity=0.8,
            style_fill_opacity=0.1,
            source_file=os.path.basename(arrondissement_file),
            srid=2154,
            visible=True
        )
        self.stdout.write(self.style.SUCCESS(f'Couche "{layer_arr.name}" créée'))

        with open(arrondissement_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        features = data.get('features', [])
        self.stdout.write(f'{len(features)} arrondissements trouvés')

        for feat in features:
            props = feat['properties']
            if not props['code'].startswith('07'):
                self.stdout.write(self.style.WARNING(
                    f'  Ignoré (hors Ardèche): {props["nom"]} ({props["code"]})'
                ))
                continue
            geom = GEOSGeometry(json.dumps(feat['geometry']), srid=4326)
            geom.transform(2154)
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon(geom)

            feature_obj = Feature.objects.create(layer=layer_arr, geom=geom)
            Arrondissement.objects.create(
                code_arrondissement=props['code'],
                nom_arrondissement=props['nom'],
                feature=feature_obj
            )
            self.stdout.write(f'  Importé: {props["nom"]} ({props["code"]})')

        # --- CANTONS ---
        existing_layer = Layer.objects.filter(name='Cantons').first()
        if existing_layer:
            if force:
                self.stdout.write(self.style.WARNING(f'Suppression de la couche existante "{existing_layer.name}"...'))
                existing_layer.delete()
            else:
                self.stdout.write(self.style.ERROR('Une couche "Cantons" existe déjà. Utilisez --force.'))
                return

        layer_canton = Layer.objects.create(
            name='Cantons',
            description='Cantons de l\'Ardèche',
            geometry_type='MultiPolygon',
            identifier_field='code_canton',
            style_color='#ff6600',
            style_weight=2,
            style_opacity=0.8,
            style_fill_opacity=0.1,
            source_file=os.path.basename(canton_file),
            srid=2154,
            visible=True
        )
        self.stdout.write(self.style.SUCCESS(f'Couche "{layer_canton.name}" créée'))

        with open(canton_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        features = data.get('features', [])
        self.stdout.write(f'{len(features)} cantons trouvés')

        for feat in features:
            props = feat['properties']
            if not props['code'].startswith('07'):
                self.stdout.write(self.style.WARNING(
                    f'  Ignoré (hors Ardèche): {props["nom"]} ({props["code"]})'
                ))
                continue
            geom = GEOSGeometry(json.dumps(feat['geometry']), srid=4326)
            geom.transform(2154)
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon(geom)

            feature_obj = Feature.objects.create(layer=layer_canton, geom=geom)

            # Lien avec arrondissement si code_arrondissement présent dans le GeoJSON
            arrondissement = None
            code_arr = props.get('code_arrondissement')
            if code_arr:
                try:
                    arrondissement = Arrondissement.objects.get(code_arrondissement=code_arr)
                except Arrondissement.DoesNotExist:
                    pass

            Canton.objects.create(
                code_canton=props['code'],
                nom_canton=props['nom'],
                arrondissement=arrondissement,
                feature=feature_obj
            )
            self.stdout.write(f'  Importé: {props["nom"]} ({props["code"]})')

        self.stdout.write(self.style.SUCCESS('\n✅ Import des cantons et arrondissements terminé !'))
