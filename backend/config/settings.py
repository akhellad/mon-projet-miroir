"""
Configuration Django pour l'Observatoire SDAEP de l'Ardèche.

Ce fichier gère la configuration du backend pour l'observatoire
des infrastructures d'alimentation en eau potable du département.
"""

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Sécurité
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Applications installées

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'rest_framework_gis',
    'corsheaders',
    'observatoire',
    'authentication',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'authentication.middleware.JWTAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Base de données PostgreSQL avec extension PostGIS
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

# Validation des mots de passe

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Fichiers statiques
STATIC_URL = 'static/'

# Configuration des clés primaires par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS - Origines autorisées pour les requêtes cross-origin
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:5173').split(',')

# Django REST Framework - Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Doit être en premier pour les appels API standards du frontend
        'authentication.authentication.JWTAuthentication',
        # Permet l'authentification via session pour la prévisualisation admin
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Par défaut, aucune permission n'est requise, elles sont définies par vue.
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Configuration du modèle User personnalisé
AUTH_USER_MODEL = 'authentication.User'

# Configuration de l'authentification JWT
from datetime import timedelta

AUTH_BACKEND = config('AUTH_BACKEND', default='authentication.backends.jwt_backend.JWTAuthBackend')
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = timedelta(hours=8)  # Durée journée de travail
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)  # Une semaine

# Configuration du logging pour le débogage
# Affiche tous les messages (DEBUG, INFO, WARNING, ERROR) dans la console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',  # Affiche les messages DEBUG et supérieurs
    },
}