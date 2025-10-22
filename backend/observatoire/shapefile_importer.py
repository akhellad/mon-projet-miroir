"""
Module pour importer des Shapefiles dans la base de données
Utilise ogr2ogr pour des performances optimales (méthode inspirée de QGIS)
"""
import os
import zipfile
import tempfile
import subprocess
import re
from django.conf import settings
from django.db import connection
from django.db.backends.utils import CursorWrapper
from .models import Layer, Feature


def import_shapefile(zip_file, layer_name, description='', identifier_field='id',
                     style_color='#3388ff', force_srid=None):
    """
    Importe un shapefile en utilisant ogr2ogr pour de meilleures performances

    Cette méthode utilise ogr2ogr en ligne de commande pour faire l'import directement
    dans PostgreSQL, offrant d'excellentes performances même pour les gros fichiers.

    Args:
        zip_file: Fichier ZIP contenant le shapefile (.shp, .dbf, .shx, .prj)
        layer_name: Nom de la couche à créer
        description: Description de la couche
        identifier_field: Champ qui sert d'identifiant unique
        style_color: Couleur de la couche
        force_srid: SRID à utiliser si non détecté automatiquement

    Returns:
        Layer: L'objet Layer créé
    """

    # Récupérer les paramètres de connexion PostgreSQL depuis Django
    db_settings = settings.DATABASES['default']
    db_name = db_settings['NAME']
    db_user = db_settings['USER']
    db_password = db_settings['PASSWORD']
    db_host = db_settings['HOST']
    db_port = db_settings['PORT']

    # Créer un dossier temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extraire le ZIP
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Trouver le fichier .shp
        shp_file = None
        for file in os.listdir(temp_dir):
            if file.endswith('.shp'):
                shp_file = os.path.join(temp_dir, file)
                break

        if not shp_file:
            raise ValueError("Aucun fichier .shp trouvé dans le ZIP")

        # Lire les métadonnées du shapefile avec GDAL
        from django.contrib.gis.gdal import DataSource
        ds = DataSource(shp_file)
        layer_gdal = ds[0]

        # Déterminer le type de géométrie
        geom_type = layer_gdal.geom_type.name
        print(f"Type de géométrie détecté: {geom_type}")

        # Normaliser le type de géométrie
        geom_type_mapping = {
            'Point': 'Point',
            'MultiPoint': 'MultiPoint',
            'LineString': 'LineString',
            'MultiLineString': 'MultiLineString',
            'Polygon': 'Polygon',
            'MultiPolygon': 'MultiPolygon',
            'Point25D': 'Point',
            'LineString25D': 'LineString',
            'Polygon25D': 'Polygon',
        }
        geometry_type = geom_type_mapping.get(geom_type, 'Polygon')

        # Récupérer le SRID source
        source_srid = layer_gdal.srs.srid if layer_gdal.srs else None

        # Utiliser force_srid si fourni
        if force_srid:
            try:
                source_srid = int(force_srid)
                # Validation : SRID doit être positif et raisonnable
                if source_srid <= 0 or source_srid > 999999:
                    raise ValueError("SRID invalide")
                print(f"SRID forcé manuellement: {source_srid}")
            except (ValueError, TypeError):
                raise ValueError("Le SRID doit être un nombre entier valide")
        elif not source_srid:
            raise ValueError("Aucun SRID trouvé dans le shapefile. Veuillez spécifier manuellement le système de coordonnées.")
        else:
            print(f"SRID détecté automatiquement: {source_srid}")

        total_features = len(layer_gdal)
        print(f"Nombre d'entités à importer: {total_features}")

        # Fermer le datasource
        ds = None
        layer_gdal = None

        # Créer la couche dans Django
        layer = Layer.objects.create(
            name=layer_name,
            description=description,
            geometry_type=geometry_type,
            identifier_field=identifier_field,
            style_color=style_color,
            source_file=zip_file.name,
            srid=2154
        )

        # Créer une table temporaire pour l'import avec ogr2ogr
        # Utiliser un nom sécurisé (uniquement alphanumériques et underscores)
        temp_table_name = f"temp_import_{layer.id}"
        # Validation du nom de table pour éviter les injections SQL
        if not re.match(r'^[a-zA-Z0-9_]+$', temp_table_name):
            raise ValueError("Nom de table temporaire invalide")

        try:
            print("Import des données avec ogr2ogr...")

            # Construire la commande ogr2ogr
            # -f PostgreSQL : format de sortie
            # -nln : nom de la table
            # -lco : options de création de couche
            # -t_srs : système de coordonnées cible (Lambert 93)
            # -s_srs : système de coordonnées source
            # -overwrite : écraser si existe
            # -progress : afficher la progression

            pg_connection = f"PG:dbname={db_name} host={db_host} port={db_port} user={db_user} password={db_password}"

            ogr2ogr_cmd = [
                'ogr2ogr',
                '-f', 'PostgreSQL',
                pg_connection,
                shp_file,
                '-nln', temp_table_name,
                '-nlt', 'GEOMETRY',  # Accepte tous les types de géométrie (Polygon, MultiPolygon, etc.)
                '-t_srs', 'EPSG:2154',
                '-s_srs', f'EPSG:{source_srid}',
                '-overwrite',
                '-progress',
                '--config', 'PG_USE_COPY', 'YES',  # Utilise COPY au lieu de INSERT (beaucoup plus rapide)
                '-lco', 'GEOMETRY_NAME=geom',
                '-lco', 'FID=ogc_fid',
                '-lco', 'PRECISION=NO'  # Évite les problèmes de précision numérique
            ]

            print(f"Commande: {' '.join(ogr2ogr_cmd)}")

            # Exécuter ogr2ogr
            result = subprocess.run(
                ogr2ogr_cmd,
                capture_output=True,
                text=True,
                env={**os.environ, 'PGPASSWORD': db_password}
            )

            if result.returncode != 0:
                print(f"Erreur ogr2ogr: {result.stderr}")
                raise Exception(f"Erreur lors de l'import avec ogr2ogr: {result.stderr}")

            print("Import ogr2ogr terminé avec succès")
            print(result.stdout)

            # Maintenant, copier les données de la table temporaire vers le modèle Feature
            print("Transfert des données vers le modèle Feature...")

            with connection.cursor() as cursor:
                # Insérer uniquement les géométries dans la table features
                # Les propriétés ne sont plus stockées en JSON car les modèles métier
                # sont définis à l'avance (Commune, Captage, UGE, etc.)
                # Utiliser quote_name pour le nom de table temporaire
                insert_query = f"""
                    INSERT INTO features (layer_id, geom, created_at, updated_at)
                    SELECT
                        %s,
                        geom,
                        NOW(),
                        NOW()
                    FROM {connection.ops.quote_name(temp_table_name)}
                """

                print(f"Exécution de la requête d'insertion...")
                cursor.execute(insert_query, [layer.id])
                inserted_count = cursor.rowcount

                print(f"✓ {inserted_count} entités insérées dans la table features")

                # Nettoyer la table temporaire
                cursor.execute(f"DROP TABLE IF EXISTS {connection.ops.quote_name(temp_table_name)}")
                print(f"Table temporaire {temp_table_name} supprimée")

        except Exception as e:
            # En cas d'erreur, nettoyer
            print(f"Erreur lors de l'import: {e}")
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {connection.ops.quote_name(temp_table_name)}")
            layer.delete()
            raise

    return layer
