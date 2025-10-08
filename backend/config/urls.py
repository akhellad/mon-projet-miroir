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
    layer_properties
)

router = DefaultRouter()
router.register(r'layers', LayerViewSet, basename='layer')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/export/commune/<str:code_insee>/', export_commune_pdf, name='export_commune_pdf'),
    path('api/preview/commune/<str:code_insee>/', preview_commune_html, name='preview_commune_html'),
    path('api/upload-shapefile/', upload_shapefile, name='upload_shapefile'),
    path('api/layers/<int:layer_id>/geojson/', layer_geojson, name='layer_geojson'),
    path('api/layers/<int:layer_id>/properties/', layer_properties, name='layer_properties'),
]
