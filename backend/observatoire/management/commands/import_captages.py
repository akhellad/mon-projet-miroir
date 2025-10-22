"""
Commande d'import des captages d'eau de l'Ardèche depuis Hub'Eau.

Cette commande récupère les ouvrages de prélèvement pour l'eau potable (AEP)
depuis l'API Hub'Eau Prélèvements et les stocke dans la base de données.

Usage:
    python manage.py import_captages [--force] [--dept 07]

Options:
    --force : Supprime la couche existante avant l'import
    --dept : Code département (défaut: 07)
"""

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from observatoire.models import Layer, Feature, Captage, Commune
import requests
import time
from datetime import datetime


class Command(BaseCommand):
    help = 'Importe les captages d\'eau de l\'Ardèche depuis Hub\'Eau API Prélèvements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Supprimer la couche Captages existante avant l\'import',
        )
        parser.add_argument(
            '--dept',
            type=str,
            default='07',
            help='Code département (défaut: 07)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('💧 IMPORT DES CAPTAGES DEPUIS HUB\'EAU'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        dept_code = options['dept']

        # Vérification de l'existence d'une couche Captages
        existing_layer = Layer.objects.filter(name='Captages').first()

        if existing_layer:
            if options['force']:
                self.stdout.write(self.style.WARNING(
                    f'Suppression de la couche existante "{existing_layer.name}"...'
                ))
                existing_layer.delete()
            else:
                self.stdout.write(self.style.ERROR(
                    'Une couche "Captages" existe déjà. Utilisez --force pour la remplacer.'
                ))
                return

        # Création de la couche Captages
        layer = Layer.objects.create(
            name='Captages',
            description=f'Captages d\'eau potable du département {dept_code} (Hub\'Eau)',
            geometry_type='Point',
            identifier_field='code_ins_captage',
            style_color='#0066cc',
            style_weight=2,  # Réduit pour des points plus petits
            style_opacity=1.0,
            style_fill_opacity=1.0,  # Opacité à 1.0 pour des points pleins
            source_file='hubeau.eaufrance.fr/api/v1/prelevements',
            srid=2154,  # Lambert 93
            visible=True
        )

        self.stdout.write(self.style.SUCCESS(f'Couche "{layer.name}" créée'))

        # Récupération des données depuis Hub'Eau avec pagination
        base_url = 'https://hubeau.eaufrance.fr/api/v1/prelevements/referentiel/ouvrages'

        # code_usage_second_niveau=5 = Eau potable (AEP)
        params = {
            'code_departement': dept_code,
            'code_usage_second_niveau': '5',  # Eau potable
            'format': 'geojson',
            'size': 1000
        }

        all_features = []
        page = 1

        try:
            while True:
                self.stdout.write(f'Récupération page {page}...')
                params['page'] = page

                response = requests.get(base_url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                features = data.get('features', [])

                if not features:
                    break

                all_features.extend(features)

                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {len(features)} captages récupérés (total: {len(all_features)})'
                ))

                # Vérifier s'il y a une page suivante
                if not data.get('next'):
                    break

                page += 1
                time.sleep(0.3)  # Rate limiting

            self.stdout.write(self.style.SUCCESS(
                f'\n📊 Total: {len(all_features)} captages trouvés'
            ))

            # Import des captages
            created_count = 0
            skipped_count = 0
            error_count = 0

            for feature_data in all_features:
                try:
                    props = feature_data['properties']
                    geometry = feature_data['geometry']

                    # Vérifier que c'est un Point
                    if geometry['type'] != 'Point':
                        self.stdout.write(self.style.WARNING(
                            f"  ⚠️ Géométrie non-Point ignorée: {props.get('nom_ouvrage')}"
                        ))
                        skipped_count += 1
                        continue

                    # Créer la géométrie (WGS84 -> Lambert 93)
                    coords = geometry['coordinates']
                    point = Point(coords[0], coords[1], srid=4326)
                    point.transform(2154)

                    # Codes de référence
                    code_ouvrage = props.get('code_ouvrage')
                    if not code_ouvrage:
                        skipped_count += 1
                        continue

                    # Vérifier si existe déjà
                    if Captage.objects.filter(code_ins_captage=code_ouvrage).exists():
                        skipped_count += 1
                        continue

                    # Créer la Feature
                    feature_obj = Feature.objects.create(
                        layer=layer,
                        geom=point
                    )

                    # Récupérer la commune par code INSEE
                    code_commune = props.get('code_commune_insee')
                    commune = None
                    if code_commune:
                        try:
                            commune = Commune.objects.get(code_insee=code_commune)
                        except Commune.DoesNotExist:
                            pass

                    # Déterminer le type de captage depuis le nom
                    nom_ouvrage = props.get('nom_ouvrage', '').upper()
                    type_captage = 'AUTRE'
                    if 'FORAGE' in nom_ouvrage:
                        type_captage = 'FORAGE'
                    elif 'SOURCE' in nom_ouvrage or 'SOURCES' in nom_ouvrage:
                        type_captage = 'SOURCE'
                    elif 'PUITS' in nom_ouvrage:
                        type_captage = 'PUITS'
                    elif 'DRAINAGE' in nom_ouvrage:
                        type_captage = 'DRAINAGE'

                    # Parser les dates
                    date_debut = None
                    date_fin = None
                    try:
                        if props.get('date_exploitation_debut'):
                            date_debut = datetime.fromisoformat(
                                props['date_exploitation_debut']
                            ).date()
                    except (ValueError, TypeError):
                        pass

                    try:
                        if props.get('date_exploitation_fin'):
                            date_fin = datetime.fromisoformat(
                                props['date_exploitation_fin']
                            ).date()
                    except (ValueError, TypeError):
                        pass

                    # Créer le Captage
                    Captage.objects.create(
                        code_ins_captage=code_ouvrage,
                        nom_captage=props.get('nom_ouvrage', 'Captage sans nom')[:200],
                        code_bss=props.get('id_local_ouvrage'),
                        code_prelev_ae=props.get('code_point_referent'),
                        commune_implantation=commune,
                        feature=feature_obj,
                        type_captage=type_captage,
                        type_usage_direct='AEP',  # Car on filtre sur code_usage=5
                        type_etat_activite_ins='ACTIF' if not date_fin else 'INACTIF',
                        type_nature_eau='EAU_BRUTE',
                        date_debut_validite_captage=date_debut,
                        date_fin_validite_captage=date_fin,
                        description_ouvrage=f"Type milieu: {props.get('libelle_type_milieu', 'N/A')}\n"
                                          f"Précision coordonnées: {props.get('libelle_precision_coord', 'N/A')}\n"
                                          f"Code BDLISA: {', '.join(props.get('codes_bdlisa', []) or [])}\n"
                                          f"URI BDLISA: {', '.join(props.get('uri_bdlisa', []) or [])}",
                        comment_generaux_captage=props.get('commentaire', '')
                    )

                    created_count += 1

                    if created_count % 50 == 0:
                        self.stdout.write(f'  ✓ {created_count} captages importés...')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ Erreur import {props.get('nom_ouvrage', 'N/A')}: {e}"
                    ))
                    continue

            self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
            self.stdout.write(self.style.SUCCESS('✅ IMPORT TERMINÉ'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS(f'✓ {created_count} captages importés'))
            self.stdout.write(self.style.WARNING(f'⊘ {skipped_count} captages ignorés (doublons ou invalides)'))
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'❌ {error_count} erreurs'))
            self.stdout.write(self.style.SUCCESS(f'Couche "{layer.name}" prête à être affichée'))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de la récupération des données: {e}'))
            layer.delete()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur inattendue: {e}'))
            layer.delete()
            raise
