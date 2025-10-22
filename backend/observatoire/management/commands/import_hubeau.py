"""
Commande Django pour importer les données Hub'Eau et enrichir les données existantes

Ce que fait ce script :
1. Importe les stations piézométriques (6 stations en Ardèche) - DONNÉES GÉOGRAPHIQUES
2. Enrichit les communes existantes avec les données UDI (qualité eau potable)

Usage:
    docker compose exec backend python manage.py import_hubeau
"""

import json
import requests
import time
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from observatoire.models import Layer, Feature


class Command(BaseCommand):
    help = "Import Hub'Eau : stations piézométriques + enrichissement communes avec UDI"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dept',
            type=str,
            default='07',
            help='Code département (défaut: 07)'
        )

    def handle(self, *args, **options):
        self.dept_code = options['dept']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🌊 IMPORT DES DONNÉES HUB\'EAU'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # 1. Import stations piézométriques (géolocalisées)
        self.import_stations_piezometrie()

        # 2. Enrichir les communes avec données UDI
        self.enrich_communes_with_udi()

        self.stdout.write(self.style.SUCCESS('\n✅ Import terminé avec succès !'))

    def fetch_hubeau(self, base_url, endpoint, params):
        """Récupère les données d'une API Hub'Eau avec pagination"""
        all_data = []
        page = 1
        size = 1000

        self.stdout.write(f"  📡 Requête {endpoint}...", ending=' ')
        self.stdout.flush()

        while True:
            params_with_page = {**params, "page": page, "size": size}

            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    params=params_with_page,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                results = data.get("data", data) if isinstance(data, dict) else data

                if not results:
                    break

                all_data.extend(results)

                if len(results) < size:
                    break

                page += 1
                time.sleep(0.3)  # Rate limiting

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.WARNING(f"\n  ⚠️ Erreur : {e}"))
                break

        self.stdout.write(self.style.SUCCESS(f"{len(all_data)} résultats"))
        return all_data

    def import_stations_piezometrie(self):
        """Import des stations piézométriques (nappes souterraines)"""
        self.stdout.write(self.style.HTTP_INFO('\n\n🌊 STATIONS PIÉZOMÉTRIQUES'))
        self.stdout.write('=' * 70)

        # Télécharger les données
        data = self.fetch_hubeau(
            "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes",
            "/stations",
            {"code_departement": self.dept_code}
        )

        if not data:
            self.stdout.write(self.style.WARNING('  ⚠️ Aucune donnée trouvée'))
            return

        # Créer ou récupérer la couche
        layer, created = Layer.objects.get_or_create(
            name='Stations piézométriques',
            defaults={
                'description': 'Stations de mesure des niveaux de nappes souterraines (Hub\'Eau)',
                'geometry_type': 'Point',
                'identifier_field': 'code_bss',
                'style_color': '#0066cc',
                'style_weight': 5,
                'style_opacity': 1.0,
                'style_fill_opacity': 0.8,
                'srid': 2154,
                'visible': True,
                'source_file': 'Hub\'Eau API - Piézométrie'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Couche créée : {layer.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'  ⚠️ Couche existante, suppression des anciennes données...'))
            layer.features.all().delete()

        # Importer les features
        features_created = 0
        for item in data:
            # Hub'Eau utilise "x" et "y" (ou "geometry")
            lon = item.get('x')
            lat = item.get('y')

            if not lon or not lat:
                # Essayer via geometry
                geom = item.get('geometry', {})
                coords = geom.get('coordinates', [])
                if len(coords) == 2:
                    lon, lat = coords
                else:
                    continue

            try:
                # Créer le point (WGS84 / CRS84 dans Hub'Eau)
                point = Point(float(lon), float(lat), srid=4326)
                # Transformer en Lambert 93
                point.transform(2154)

                # Créer la feature
                Feature.objects.create(
                    layer=layer,
                    geom=point,
                    properties={
                        'code_bss': item.get('code_bss', 'N/A'),
                        'nom_station': item.get('libelle_pe', ''),
                        'code_commune_insee': item.get('code_commune_insee', ''),
                        'nom_commune': item.get('nom_commune', ''),
                        'date_debut_mesure': item.get('date_debut_mesure') or '',
                        'date_fin_mesure': item.get('date_fin_mesure') or '',
                        'profondeur_investigation': item.get('profondeur_investigation') or 0,
                        'altitude_station': item.get('altitude_station') or 0,
                        'nb_mesures': item.get('nb_mesures_piezo', 0),
                        'codes_bdlisa': ', '.join(item.get('codes_bdlisa', [])),
                        'masse_eau': ', '.join(item.get('noms_masse_eau_edl', [])),
                    }
                )
                features_created += 1

            except (ValueError, TypeError) as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Erreur feature {item.get("code_bss")}: {e}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'  ✅ {features_created} stations importées'))

    def enrich_communes_with_udi(self):
        """Enrichit les communes existantes avec les données UDI (qualité eau potable)"""
        self.stdout.write(self.style.HTTP_INFO('\n\n🚰 ENRICHISSEMENT COMMUNES AVEC UDI'))
        self.stdout.write('=' * 70)

        # Vérifier si la couche Communes existe
        try:
            communes_layer = Layer.objects.get(name='Communes')
        except Layer.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠️ Couche "Communes" non trouvée, import ignoré'))
            self.stdout.write('  💡 Importez d\'abord les communes avec : python manage.py import_communes')
            return

        # Récupérer toutes les communes de l'Ardèche
        communes_features = communes_layer.features.all()
        nb_communes = communes_features.count()

        if nb_communes == 0:
            self.stdout.write(self.style.WARNING('  ⚠️ Aucune commune dans la BDD'))
            return

        self.stdout.write(f'  📊 {nb_communes} communes trouvées dans la BDD')

        # Télécharger les données UDI
        self.stdout.write('\n  📡 Téléchargement des données UDI Hub\'Eau...')

        # Récupérer les codes INSEE des communes existantes
        codes_insee = [
            f.properties.get('code_insee') or f.properties.get('code') or f.properties.get('insee')
            for f in communes_features
        ]
        codes_insee = [c for c in codes_insee if c and c.startswith(self.dept_code)]

        if not codes_insee:
            self.stdout.write(self.style.WARNING('  ⚠️ Aucun code INSEE trouvé dans les communes'))
            return

        self.stdout.write(f'  📍 {len(codes_insee)} codes INSEE identifiés')

        # Télécharger UDI pour toutes les communes
        udi_data = []
        batch_size = 50
        for i in range(0, len(codes_insee), batch_size):
            batch = codes_insee[i:i+batch_size]
            self.stdout.write(f'  📥 Batch {i//batch_size + 1}/{(len(codes_insee)-1)//batch_size + 1}...', ending=' ')
            self.stdout.flush()

            for code in batch:
                try:
                    response = requests.get(
                        "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/communes_udi",
                        params={"code_commune": code, "size": 100},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("data", [])
                        udi_data.extend(results)
                    time.sleep(0.1)
                except:
                    pass

            self.stdout.write(self.style.SUCCESS(f'{len(udi_data)} UDI cumulées'))

        if not udi_data:
            self.stdout.write(self.style.WARNING('  ⚠️ Aucune donnée UDI récupérée'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n  ✅ {len(udi_data)} UDI récupérées au total'))

        # Grouper par commune
        udi_by_commune = {}
        for udi in udi_data:
            code = udi.get('code_commune')
            if code not in udi_by_commune:
                udi_by_commune[code] = []
            udi_by_commune[code].append(udi)

        # Enrichir les communes
        enriched_count = 0
        for commune_feature in communes_features:
            code_insee = (
                commune_feature.properties.get('code_insee') or
                commune_feature.properties.get('code') or
                commune_feature.properties.get('insee')
            )

            if code_insee in udi_by_commune:
                udis = udi_by_commune[code_insee]

                # Ajouter les infos UDI dans les propriétés
                commune_feature.properties['nb_udi'] = len(udis)
                commune_feature.properties['reseaux_udi'] = [
                    {
                        'code_reseau': u.get('code_reseau'),
                        'nom_reseau': u.get('nom_reseau'),
                        'debut_alim': u.get('debut_alim')
                    }
                    for u in udis
                ]

                commune_feature.save()
                enriched_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✅ {enriched_count} communes enrichies avec données UDI'))
