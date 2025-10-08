"""
Configuration ASGI pour l'Observatoire SDAEP.

Point d'entrée ASGI pour le déploiement avec serveurs compatibles ASGI
(Daphne, Uvicorn, etc.).
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
