"""
Configuration des URLs pour l'Observatoire SDAEP.

Définit les routes de l'API REST et de l'interface d'administration.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from observatoire.views import (
    LayerViewSet,
    export_commune_pdf,
    preview_commune_html,
    upload_shapefile,
    layer_geojson,
    layer_properties,
    reorder_layers
)

router = DefaultRouter()
router.register(r'layers', LayerViewSet, basename='layer')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Routes d'authentification
    path('api/auth/', include('authentication.urls')),
    # Routes spécifiques AVANT le router pour éviter les conflits
    path('api/layers/reorder/', reorder_layers, name='reorder_layers'),
    path('api/layers/<int:layer_id>/geojson/', layer_geojson, name='layer_geojson'),
    path('api/layers/<int:layer_id>/properties/', layer_properties, name='layer_properties'),
    path('api/export/commune/<str:code_insee>/', export_commune_pdf, name='export_commune_pdf'),
    path('api/preview/commune/<str:code_insee>/', preview_commune_html, name='preview_commune_html'),
    path('api/upload-shapefile/', upload_shapefile, name='upload_shapefile'),
    # Router DRF (doit être après les routes spécifiques)
    path('api/', include(router.urls)),
]
