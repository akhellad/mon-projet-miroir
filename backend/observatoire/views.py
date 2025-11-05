from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.clickjacking import xframe_options_exempt
from weasyprint import HTML
from datetime import datetime
from .models import Layer, Commune
from .serializers import LayerSerializer, FeatureSerializer
from .charts import (
    generate_top_communes_chart,
    generate_population_pie_chart,
    generate_population_distribution_bar_chart
)
from .shapefile_importer import import_shapefile
from authentication.permissions import (
    RoleBasedPermission,
    CanUploadShapefile,
    CanExportData,
    IsLecteurOrAbove
)


class LayerViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des couches géographiques.

    Permissions:
    - GET: Lecteur, Contributeur, Admin
    - POST: Contributeur, Admin
    - PATCH/PUT: Contributeur, Admin
    - DELETE: Admin uniquement
    """
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
    permission_classes = [RoleBasedPermission]


@api_view(['GET'])
@permission_classes([IsLecteurOrAbove])
def layer_geojson(request, layer_id):
    """
    Retourne toutes les features d'une couche au format GeoJSON
    Optimisé pour les grosses couches avec transformation SQL

    Permissions: Lecteur, Contributeur, Admin
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
            # Note: Cette requête SQL doit être adaptée car properties n'existe plus
            # Les propriétés doivent maintenant être récupérées depuis les tables métier
            cursor.execute("""
                SELECT json_build_object(
                    'type', 'FeatureCollection',
                    'features', json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'id', id,
                            'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::json,
                            'properties', json_build_object('id', id)
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
@permission_classes([IsLecteurOrAbove])
def layer_properties(request, layer_id):
    """
    Retourne uniquement les propriétés des features (sans géométries) pour optimiser les stats
    Utilise le serializer pour extraire automatiquement les propriétés des modèles métier

    Permissions: Lecteur, Contributeur, Admin
    """
    try:
        layer = Layer.objects.get(id=layer_id)
    except Layer.DoesNotExist:
        return Response({'error': 'Couche non trouvée'}, status=404)

    # Utiliser le serializer pour extraire les propriétés
    # select_related pour optimiser les requêtes
    features = layer.features.select_related(
        'commune', 'captage', 'uge', 'udi', 'canton', 'arrondissement'
    ).all()
    serializer = FeatureSerializer(features, many=True)

    # Le GeoFeatureModelSerializer retourne un GeoJSON avec type, geometry, properties
    # Extraire uniquement les propriétés
    result = {
        'type': 'PropertiesCollection',
        'count': len(features),
        'features': [
            {
                'id': feature_geojson.get('id'),
                'properties': feature_geojson.get('properties', {})
            }
            for feature_geojson in serializer.data.get('features', [])
        ]
    }

    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([CanUploadShapefile])
def upload_shapefile(request):
    """
    Upload et import d'un shapefile (fichier ZIP)
    Utilise ogr2ogr pour des performances optimales

    Permissions: Contributeur, Admin
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
@permission_classes([CanExportData])
def export_commune_pdf(request, code_insee):
    """
    Génère et retourne un PDF de fiche de synthèse pour une commune

    Permissions: Contributeur, Admin
    """
    try:
        # Récupérer directement la commune depuis le modèle métier
        commune = Commune.objects.get(code_insee=code_insee)

    except Commune.DoesNotExist:
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
@permission_classes([IsLecteurOrAbove])
def preview_commune_html(request, code_insee):
    """
    Retourne le HTML de prévisualisation pour une commune (même template que le PDF)
    """
    try:
        # Récupérer directement la commune depuis le modèle métier
        commune = Commune.objects.get(code_insee=code_insee)

    except Commune.DoesNotExist:
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


@api_view(['POST'])
@permission_classes([IsLecteurOrAbove])
def reorder_layers(request):
    """
    Met à jour l'ordre des couches pour gérer le z-index
    Attend un payload: { "layers": [{"id": 1, "order": 0}, {"id": 2, "order": 1}, ...] }

    Permissions: Lecteur, Contributeur, Admin (tous peuvent réorganiser leur vue)
    """
    layers_data = request.data.get('layers', [])

    if not layers_data:
        return Response({'error': 'Aucune donnée de couches fournie'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Mise à jour en masse pour de meilleures performances
        for layer_data in layers_data:
            Layer.objects.filter(id=layer_data['id']).update(order=layer_data['order'])

        return Response({'success': True, 'message': f'{len(layers_data)} couches réordonnées'})

    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la réorganisation: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
