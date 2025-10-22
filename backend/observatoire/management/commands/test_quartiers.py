from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, MultiPolygon
from django.db import transaction
from observatoire.models import UDI, Commune, Layer, Feature
import requests
from time import sleep


class Command(BaseCommand):
    help = 'Géoréférence les UDI en fonction des communes et quartiers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recréer les géométries existantes',
        )

    def geocode_quartier_ban(self, nom_quartier, code_commune):
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {
            "q": nom_quartier,
            "citycode": code_commune,
            "type": "locality",
            "limit": 1
        }
        
        try:
            r = requests.get(url, params=params, timeout=5)
            if r.ok:
                data = r.json()
                if data.get("features") and data["features"][0]["properties"].get("score", 0) > 0.4:
                    coords = data["features"][0]["geometry"]["coordinates"]
                    return Point(coords[0], coords[1], srid=4326)
        except:
            pass
        return None

    def geocode_quartier_osm(self, nom_quartier, nom_commune):
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{nom_quartier}, {nom_commune}, Ardèche, France",
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "UDI-Ardeche-Geocoder/1.0"}
        
        try:
            sleep(1.1)
            r = requests.get(url, params=params, headers=headers, timeout=5)
            if r.ok:
                data = r.json()
                if data:
                    return Point(float(data[0]["lon"]), float(data[0]["lat"]), srid=4326)
        except:
            pass
        return None

    def get_commune_geom(self, commune):
        if commune.feature and commune.feature.geom:
            return commune.feature.geom
        return None

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Début du géoréférencement des UDI...'))

        layer = Layer.objects.filter(name='UDI').first()
        if not layer:
            self.stdout.write(self.style.ERROR('Couche UDI introuvable'))
            return

        udis = UDI.objects.all()
        
        if not options['force']:
            udis = udis.filter(feature__isnull=True)
        
        total = udis.count()
        self.stdout.write(f'📊 {total} UDI à géoréférencer')

        stats = {
            'mono_commune_sans_quartier': 0,
            'mono_commune_avec_quartier_trouve': 0,
            'mono_commune_avec_quartier_centroid': 0,
            'multi_communes': 0,
            'erreurs': 0
        }

        with transaction.atomic():
            for idx, udi in enumerate(udis, 1):
                try:
                    communes = list(udi.communes.all())
                    nb_communes = len(communes)
                    
                    if nb_communes == 0:
                        self.stdout.write(self.style.WARNING(
                            f'⚠️  UDI {udi.code_ins_udi}: aucune commune associée'
                        ))
                        stats['erreurs'] += 1
                        continue

                    geom = None
                    methode = ""

                    # CAS 1: UDI mono-commune SANS quartier spécifique
                    if nb_communes == 1 and (not udi.nom_quartier or udi.nom_quartier == "-"):
                        commune = communes[0]
                        commune_geom = self.get_commune_geom(commune)
                        
                        if commune_geom:
                            # Utiliser le contour complet de la commune
                            geom = commune_geom
                            if geom.geom_type == 'Polygon':
                                geom = MultiPolygon(geom, srid=2154)
                            methode = "contour_commune"
                            stats['mono_commune_sans_quartier'] += 1

                    # CAS 2: UDI mono-commune AVEC quartier(s)
                    elif nb_communes == 1 and udi.nom_quartier and udi.nom_quartier != "-":
                        commune = communes[0]
                        quartiers = [q.strip() for q in udi.nom_quartier.split(",")]
                        
                        # Essayer de géocoder le premier quartier
                        premier_quartier = quartiers[0]
                        point = self.geocode_quartier_ban(premier_quartier, commune.code_insee)
                        
                        if not point:
                            point = self.geocode_quartier_osm(premier_quartier, commune.nom)
                        
                        if point:
                            point.transform(2154)
                            geom = point
                            methode = f"quartier_geocode ({premier_quartier})"
                            stats['mono_commune_avec_quartier_trouve'] += 1
                        else:
                            # Fallback: centroïde de la commune
                            commune_geom = self.get_commune_geom(commune)
                            if commune_geom:
                                geom = commune_geom.centroid
                                methode = f"centroid_commune (quartier '{premier_quartier}' non trouvé)"
                                stats['mono_commune_avec_quartier_centroid'] += 1

                    # CAS 3: UDI multi-communes
                    else:
                        polygons = []
                        for commune in communes:
                            commune_geom = self.get_commune_geom(commune)
                            if commune_geom:
                                if commune_geom.geom_type == 'Polygon':
                                    polygons.append(commune_geom)
                                elif commune_geom.geom_type == 'MultiPolygon':
                                    polygons.extend(list(commune_geom))
                        
                        if polygons:
                            geom = MultiPolygon(polygons, srid=2154)
                            methode = f"union_{nb_communes}_communes"
                            stats['multi_communes'] += 1

                    # Créer ou mettre à jour la feature
                    if geom:
                        if options['force'] and udi.feature:
                            udi.feature.geom = geom
                            udi.feature.save()
                        else:
                            feature = Feature.objects.create(
                                layer=layer,
                                geom=geom
                            )
                            udi.feature = feature
                            udi.save()
                        
                        if idx % 50 == 0:
                            self.stdout.write(
                                f'  ... {idx}/{total} UDI traitées'
                            )
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'⚠️  UDI {udi.code_ins_udi}: impossible de créer une géométrie'
                        ))
                        stats['erreurs'] += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'❌ Erreur UDI {udi.code_ins_udi}: {str(e)}'
                    ))
                    stats['erreurs'] += 1

        self.stdout.write(self.style.SUCCESS('\n✅ Géoréférencement terminé'))
        self.stdout.write('\n📊 Statistiques:')
        self.stdout.write(f"   Mono-commune sans quartier (contour): {stats['mono_commune_sans_quartier']}")
        self.stdout.write(f"   Mono-commune avec quartier géocodé: {stats['mono_commune_avec_quartier_trouve']}")
        self.stdout.write(f"   Mono-commune avec quartier (centroid fallback): {stats['mono_commune_avec_quartier_centroid']}")
        self.stdout.write(f"   Multi-communes (union): {stats['multi_communes']}")
        self.stdout.write(f"   Erreurs: {stats['erreurs']}")