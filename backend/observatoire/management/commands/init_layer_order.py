"""
Commande de gestion pour initialiser l'ordre des couches existantes.

Usage:
    python manage.py init_layer_order
"""

from django.core.management.base import BaseCommand
from observatoire.models import Layer


class Command(BaseCommand):
    help = 'Initialise le champ order des couches existantes'

    def handle(self, *args, **options):
        # Récupérer toutes les couches qui ont order=0
        layers = Layer.objects.filter(order=0).order_by('id')
        total = layers.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Toutes les couches ont déjà un ordre défini.'))
            return

        self.stdout.write(f'Initialisation de l\'ordre pour {total} couches...')

        # Assigner un ordre décroissant (première couche = order le plus élevé)
        for i, layer in enumerate(layers):
            layer.order = total - i
            layer.save(update_fields=['order'])
            self.stdout.write(f'  - {layer.name}: order = {layer.order}')

        self.stdout.write(self.style.SUCCESS(f'✓ {total} couches initialisées avec succès.'))
