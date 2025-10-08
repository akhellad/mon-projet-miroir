"""
Configuration WSGI pour l'Observatoire SDAEP.

Point d'entrée WSGI pour le déploiement avec serveurs compatibles WSGI
(Gunicorn, uWSGI, etc.).
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
