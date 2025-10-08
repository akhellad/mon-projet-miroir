from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.clickjacking import xframe_options_exempt
from weasyprint import HTML
from datetime import datetime
from .models import Layer, Feature
from .serializers import LayerSerializer, FeatureSerializer
from .charts import (
    generate_top_communes_chart,
    generate_population_pie_chart,
    generate_population_distribution_bar_chart
)
from .shapefile_importer import import_shapefile


class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer


@api_view(['GET'])
def layer_geojson(request, layer_id):
    """
    Retourne toutes les features d'une couche au format GeoJSON
    Optimisé pour les grosses couches avec transformation SQL
    """
    try:
        layer = Layer.objects.get(id=layer_id)
    except Layer.DoesNotExist:
        return Response({'error': 'Couche non trouvée'}, status=404)

    # Pour les grosses couches (>10000 features), utiliser une réponse SQL optimisée
    feature_count = layer.features.count()

    if feature_count > 10000:
        # Transformation SQL directe pour de meilleures performances
        from django.db import connection
        from django.http import JsonResponse
        import time

        print(f"[{layer.name}] Chargement de {feature_count} features avec optimisation SQL...")
        start = time.time()

        with connection.cursor() as cursor:
            # Important : ST_AsGeoJSON retourne du TEXT, il faut le caster en jsonb
            cursor.execute("""
                SELECT json_build_object(
                    'type', 'FeatureCollection',
                    'features', json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'id', id,
                            'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::json,
                            'properties', properties
                        )
                    )
                )
                FROM features
                WHERE layer_id = %s
            """, [layer_id])

            result = cursor.fetchone()[0]
            elapsed = time.time() - start
            print(f"[{layer.name}] Chargé en {elapsed:.2f}s")
            return JsonResponse(result, safe=False)

    # Pour les petites couches, utiliser le serializer standard
    features = layer.features.all()
    serializer = FeatureSerializer(features, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def layer_properties(request, layer_id):
    """
    Retourne uniquement les propriétés des features (sans géométries) pour optimiser les stats
    """
    try:
        layer = Layer.objects.get(id=layer_id)
    except Layer.DoesNotExist:
        return Response({'error': 'Couche non trouvée'}, status=404)

    # Récupérer uniquement les properties, pas les géométries
    features = layer.features.all().values('id', 'properties')

    # Formater comme un FeatureCollection simplifié
    result = {
        'type': 'PropertiesCollection',
        'count': len(features),
        'features': [
            {
                'id': f['id'],
                'properties': f['properties']
            }
            for f in features
        ]
    }

    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_shapefile(request):
    """
    Upload et import d'un shapefile (fichier ZIP)
    Utilise ogr2ogr pour des performances optimales
    """
    if 'file' not in request.FILES:
        return Response({'error': 'Aucun fichier fourni'}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    layer_name = request.data.get('name', 'Nouvelle couche')
    description = request.data.get('description', '')
    identifier_field = request.data.get('identifier_field', 'id')
    style_color = request.data.get('style_color', '#3388ff')
    force_srid = request.data.get('force_srid')  # Optionnel

    # Vérifier que c'est un fichier ZIP
    if not file.name.endswith('.zip'):
        return Response(
            {'error': 'Le fichier doit être un fichier ZIP contenant un shapefile'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Import avec ogr2ogr (optimisé pour tous les fichiers)
        layer = import_shapefile(
            file,
            layer_name,
            description,
            identifier_field,
            style_color,
            force_srid=force_srid
        )

        serializer = LayerSerializer(layer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'import: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def export_commune_pdf(request, code_insee):
    """
    Génère et retourne un PDF de fiche de synthèse pour une commune
    """
    try:
        # Récupérer la couche Communes
        communes_layer = Layer.objects.get(name='Communes')
        # Récupérer la commune via son code INSEE
        commune_feature = Feature.objects.get(
            layer=communes_layer,
            properties__code_insee=code_insee
        )

        # Créer un objet compatible avec le template
        class CommuneCompat:
            def __init__(self, feature):
                self.nom = feature.properties.get('nom')
                self.code_insee = feature.properties.get('code_insee')
                self.population = feature.properties.get('population')
                self.geom = feature.geom

        commune = CommuneCompat(commune_feature)

    except (Layer.DoesNotExist, Feature.DoesNotExist):
        return Response({'error': 'Commune non trouvée'}, status=404)

    # Génération des graphiques (similaires au dashboard)
    top_communes_chart = generate_top_communes_chart()
    pie_chart = generate_population_pie_chart()
    distribution_chart = generate_population_distribution_bar_chart()

    # Données du contexte pour le template
    context = {
        'commune': commune,
        'date_generation': datetime.now().strftime('%d/%m/%Y'),
        'top_communes_chart': top_communes_chart,
        'pie_chart': pie_chart,
        'distribution_chart': distribution_chart,
    }

    # Rendu du template HTML
    html_string = render_to_string('observatoire/fiche_commune.html', context)

    # Génération du PDF avec WeasyPrint
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    # Retour de la réponse HTTP avec le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_{commune.nom}_{code_insee}.pdf"'

    return response

@api_view(['GET'])
@xframe_options_exempt
def preview_commune_html(request, code_insee):
    """
    Retourne le HTML de prévisualisation pour une commune (même template que le PDF)
    """
    try:
        # Récupérer la couche Communes
        communes_layer = Layer.objects.get(name='Communes')
        # Récupérer la commune via son code INSEE
        commune_feature = Feature.objects.get(
            layer=communes_layer,
            properties__code_insee=code_insee
        )

        # Créer un objet compatible avec le template
        class CommuneCompat:
            def __init__(self, feature):
                self.nom = feature.properties.get('nom')
                self.code_insee = feature.properties.get('code_insee')
                self.population = feature.properties.get('population')
                self.geom = feature.geom

        commune = CommuneCompat(commune_feature)

    except (Layer.DoesNotExist, Feature.DoesNotExist):
        return Response({'error': 'Commune non trouvée'}, status=404)

    # Génération des graphiques (similaires au dashboard)
    top_communes_chart = generate_top_communes_chart()
    pie_chart = generate_population_pie_chart()
    distribution_chart = generate_population_distribution_bar_chart()

    # Données du contexte pour le template
    context = {
        'commune': commune,
        'date_generation': datetime.now().strftime('%d/%m/%Y'),
        'preview_mode': True,  # Mode aperçu
        'top_communes_chart': top_communes_chart,
        'pie_chart': pie_chart,
        'distribution_chart': distribution_chart,
    }

    # Rendu du template HTML
    html_string = render_to_string('observatoire/fiche_commune.html', context)

    return HttpResponse(html_string, content_type='text/html')
