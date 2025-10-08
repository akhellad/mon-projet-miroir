#!/bin/bash

set -e

# Attendre que PostgreSQL soit prêt
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Appliquer les migrations
python manage.py migrate

# Créer un superuser si non existant
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Lancer le serveur
python manage.py runserver 0.0.0.0:8000