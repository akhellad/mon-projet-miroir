# Guide d'installation - Observatoire SDAEP

Ce guide détaille l'installation complète du projet, de la configuration initiale au premier lancement.

---

## Prérequis système

### Logiciels requis

| Logiciel       | Version minimale | Notes                                    |
|----------------|------------------|------------------------------------------|
| Docker         | 24.0+            | Containerisation des services            |
| Docker Compose | 2.0+             | Orchestration multi-conteneurs           |
| Git            | 2.30+            | Gestion de version                       |
| Make           | 4.0+ (optionnel) | Simplification des commandes             |

### Vérification des prérequis

```bash
# Vérifier Docker
docker --version
# Attendu: Docker version 24.0.0 ou supérieur

# Vérifier Docker Compose
docker compose version
# Attendu: Docker Compose version v2.0.0 ou supérieur

# Vérifier Git
git --version
# Attendu: git version 2.30.0 ou supérieur

# Vérifier Make (optionnel)
make --version
# Attendu: GNU Make 4.x
```

### Configuration système recommandée

**Développement**
- CPU : 4 cores minimum
- RAM : 8 GB minimum (16 GB recommandé)
- Disque : 20 GB libres
- OS : Linux, macOS, Windows (avec WSL2)

**Production**
- CPU : 8 cores
- RAM : 16 GB
- Disque : 100 GB SSD
- OS : Linux (Ubuntu 22.04 LTS ou Debian 12)

---

## Installation pas à pas

### 1. Récupération du code source

```bash
# Cloner le dépôt Git
git clone https://github.com/votre-organisation/sdaep-observatoire.git
cd sdaep-observatoire

# Vérifier la branche
git branch
# Vous devriez être sur 'main'
```

### 2. Configuration des variables d'environnement

Le fichier `.env` contient toutes les configurations sensibles du projet.

```bash
# Copier le template d'environnement
cp .env.example .env
```

**Éditer le fichier `.env` avec vos valeurs :**

```bash
# Éditeur de votre choix
nano .env
# ou
vim .env
# ou
code .env  # VSCode
```

**Variables critiques à configurer :**

```bash
# ============================================
# BASE DE DONNÉES
# ============================================
DB_NAME=sdaep_ardeche
DB_USER=sdaep_user
DB_PASSWORD=CHANGEZ_MOI_MIN_20_CARACTERES_SECURISES
DB_HOST=db
DB_PORT=5432

# ============================================
# DJANGO
# ============================================
# Générer une clé secrète sécurisée (50+ caractères)
# Vous pouvez utiliser : python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=django-insecure-CHANGEZ_MOI_MINIMUM_50_CARACTERES

# Mode debug (TOUJOURS False en production)
DEBUG=True

# ============================================
# SUPERUSER (compte admin Django)
# ============================================
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=CHANGEZ_MOI_MIN_20_CARACTERES

# ============================================
# SÉCURITÉ
# ============================================
# En développement
ALLOWED_HOSTS=localhost,127.0.0.1

# En production, ajouter votre domaine :
# ALLOWED_HOSTS=observatoire.ardeche.fr,localhost,127.0.0.1

# ============================================
# CORS (Cross-Origin Resource Sharing)
# ============================================
# En développement
CORS_ALLOWED_ORIGINS=http://localhost:5173

# En production, ajouter votre domaine :
# CORS_ALLOWED_ORIGINS=https://observatoire.ardeche.fr,http://localhost:5173

# ============================================
# FRONTEND
# ============================================
VITE_ADMIN_URL=http://localhost:8000/admin/

# ============================================
# OIDC (Optionnel - authentification SSO)
# ============================================
# À configurer si vous utilisez un SSO
OIDC_RP_CLIENT_ID=
OIDC_RP_CLIENT_SECRET=
OIDC_OP_DISCOVERY_ENDPOINT=
OIDC_RP_CALLBACK_URL=http://localhost:8000/oidc/callback/
```

**🔐 Génération de mots de passe sécurisés :**

```bash
# Générer un mot de passe aléatoire de 32 caractères
openssl rand -base64 32

# Générer une clé secrète Django
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Construction des images Docker

```bash
# Avec Make (recommandé)
make build

# Ou directement avec Docker Compose
docker compose build
```

**Temps estimé :** 5-10 minutes (dépend de votre connexion internet)

**Détails de la construction :**
- 🐍 Backend : Installation de Django, GeoDjango, PostGIS, WeasyPrint
- ⚛️ Frontend : Installation de React, Vite, Leaflet, dépendances npm
- 🗄️ Base de données : Image PostgreSQL 16 + PostGIS 3.4 (pré-construite)

### 4. Démarrage des services

```bash
# Démarrer tous les conteneurs en arrière-plan
make up

# Ou avec Docker Compose
docker compose up -d
```

**Vérification du démarrage :**

```bash
# Voir l'état des conteneurs
make status

# Ou
docker compose ps
```

**Sortie attendue :**
```
NAME                IMAGE                      STATUS         PORTS
sdaep_backend       sdaep-observatoire-backend   Up 30 seconds  0.0.0.0:8000->8000/tcp
sdaep_frontend      sdaep-observatoire-frontend  Up 30 seconds  0.0.0.0:5173->5173/tcp
sdaep_postgres      postgis/postgis:16-3.4       Up 30 seconds  0.0.0.0:5432->5432/tcp
```

### 5. Initialisation de la base de données

#### 5.1. Appliquer les migrations Django

Les migrations créent les tables nécessaires dans PostgreSQL.

```bash
# Appliquer les migrations
make migrate

# Ou
docker compose exec backend python manage.py migrate
```

**Sortie attendue :**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, observatoire, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying observatoire.0001_initial... OK
  ...
```

#### 5.2. Créer un superutilisateur Django

Le superuser permet d'accéder à l'interface d'administration Django.

```bash
# Créer un superuser interactif
make createsuperuser

# Ou
docker compose exec backend python manage.py createsuperuser
```

**Prompts attendus :**
```
Username: admin
Email address: admin@naldeo.fr
Password: ********
Password (again): ********
Superuser created successfully.
```

**Note :** Vous pouvez aussi utiliser les variables `SUPERUSER_USERNAME` et `SUPERUSER_PASSWORD` du `.env` pour créer automatiquement le superuser au démarrage (voir section Automatisation).

### 6. Vérification de l'installation

#### 6.1. Vérifier les logs

```bash
# Voir tous les logs
make logs

# Logs backend uniquement
make logs-backend

# Logs frontend uniquement
make logs-frontend

# Logs base de données
make logs-db
```

**Logs backend attendus (pas d'erreurs) :**
```
sdaep_backend | Watching for file changes with StatReloader
sdaep_backend | Performing system checks...
sdaep_backend | System check identified no issues (0 silenced).
sdaep_backend | Django version 5.2.6, using settings 'config.settings'
sdaep_backend | Starting development server at http://0.0.0.0:8000/
```

#### 6.2. Tester les URLs

Ouvrir dans un navigateur :

**Frontend (Interface utilisateur)**
```
http://localhost:5173
```
Vous devriez voir la carte interactive.

**Backend API (Endpoints REST)**
```
http://localhost:8000/api/
```
Vous devriez voir l'interface Django REST Framework.

**Admin Django**
```
http://localhost:8000/admin/
```
Connectez-vous avec le superuser créé à l'étape 5.2.

#### 6.3. Tester la connexion à la base de données

```bash
# Ouvrir un shell PostgreSQL
make db-shell

# Ou
docker compose exec db psql -U sdaep_user -d sdaep_ardeche
```

**Dans le shell PostgreSQL :**
```sql
-- Vérifier l'extension PostGIS
SELECT PostGIS_Version();

-- Lister les tables
\dt

-- Quitter
\q
```

---

## Automatisation de l'initialisation

Pour automatiser la création du superuser et d'autres tâches au premier démarrage, vous pouvez créer un script d'initialisation.

**Créer `backend/init.sh` :**

```bash
#!/bin/bash
set -e

echo "🔄 Application des migrations..."
python manage.py migrate --no-input

echo "Création du superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('SUPERUSER_USERNAME', 'admin')
password = os.environ.get('SUPERUSER_PASSWORD', 'admin')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, '', password)
    print(f"Superuser '{username}' créé")
else:
    print(f"ℹSuperuser '{username}' existe déjà")
EOF

echo "Initialisation terminée"
```

**Modifier le `backend/Dockerfile` pour exécuter ce script :**

```dockerfile
# À ajouter à la fin du Dockerfile
COPY init.sh /app/init.sh
RUN chmod +x /app/init.sh

CMD ["/bin/bash", "-c", "/app/init.sh && python manage.py runserver 0.0.0.0:8000"]
```

---

## Import de données initiales

### Import d'un ShapeFile

```bash
# Depuis l'interface web
1. Aller sur http://localhost:5173
2. Cliquer sur "Importer une couche"
3. Sélectionner un fichier .zip contenant :
   - fichier.shp
   - fichier.dbf
   - fichier.shx
   - fichier.prj
4. Définir le nom de la couche et le type de géométrie
5. Valider l'import
```

**Ou via l'API directement :**

```bash
curl -X POST http://localhost:8000/api/upload-shapefile/ \
  -F "file=@communes_ardeche.zip" \
  -F "layer_name=Communes Ardèche" \
  -F "geometry_type=Polygon"
```

### Import de données QGIS

Si vous avez déjà des projets QGIS connectés à une base PostGIS :

```bash
# 1. Exporter une couche depuis QGIS au format ShapeFile
# 2. Compresser les fichiers en .zip
# 3. Utiliser l'interface d'import (ci-dessus)
```

---

## Dépannage (Troubleshooting)

### Problème : Le backend ne démarre pas

**Erreur possible :**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solution :**
```bash
# Vérifier que la base de données est bien démarrée
docker compose ps

# Si le service 'db' n'est pas 'Up', le redémarrer
docker compose restart db

# Attendre le healthcheck, puis redémarrer le backend
docker compose restart backend
```

### Problème : Le frontend affiche une page blanche

**Solution :**
```bash
# Vérifier les logs frontend
make logs-frontend

# Reconstruire le frontend
docker compose down
docker compose build frontend
docker compose up -d
```

### Problème : Erreur de permissions sur les fichiers

**Erreur possible :**
```
PermissionError: [Errno 13] Permission denied
```

**Solution (Linux/macOS) :**
```bash
# Ajuster les permissions du dossier
sudo chown -R $USER:$USER .

# Ou exécuter les commandes Docker avec sudo
sudo docker compose up -d
```

### Problème : Port déjà utilisé

**Erreur possible :**
```
Error starting userland proxy: listen tcp4 0.0.0.0:5432: bind: address already in use
```

**Solution :**
```bash
# Identifier le processus utilisant le port
sudo lsof -i :5432

# Tuer le processus (remplacer PID par le numéro trouvé)
sudo kill -9 PID

# Ou modifier le port dans docker-compose.yml
# Remplacer "5432:5432" par "5433:5432" (port hôte 5433)
```

### Problème : Migrations en échec

**Solution :**
```bash
# Réinitialiser complètement la base de données
make clean       # Supprime conteneurs ET volumes
make build
make up
make migrate
make createsuperuser
```

### Problème : Le serveur Django retourne une erreur CORS

**Erreur dans le navigateur :**
```
Access to fetch at 'http://localhost:8000/api/layers/' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**Solution :**
```bash
# Vérifier que CORS_ALLOWED_ORIGINS contient bien http://localhost:5173
cat .env | grep CORS_ALLOWED_ORIGINS

# Si absent, ajouter dans .env :
echo "CORS_ALLOWED_ORIGINS=http://localhost:5173" >> .env

# Redémarrer le backend
docker compose restart backend
```

---

## Arrêt et nettoyage

### Arrêter les services

```bash
# Arrêter proprement
make down

# Ou
docker compose down
```

### Nettoyage complet (⚠️ Supprime les données)

```bash
# Supprimer conteneurs + volumes (données perdues)
make clean

# Ou
docker compose down -v
```

### Reconstruire de zéro

```bash
# Tout nettoyer et reconstruire
make rebuild

# Ou
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Checklist de validation post-installation

Après l'installation, vérifier :

- [ ] Les 3 services Docker sont démarrés (`docker compose ps`)
- [ ] Le frontend est accessible sur http://localhost:5173
- [ ] L'API répond sur http://localhost:8000/api/
- [ ] L'admin Django fonctionne sur http://localhost:8000/admin/
- [ ] Les logs backend ne montrent pas d'erreur
- [ ] Les logs frontend ne montrent pas d'erreur
- [ ] La base de données accepte les connexions
- [ ] L'extension PostGIS est activée (`SELECT PostGIS_Version();`)
- [ ] Un superuser a été créé et permet de se connecter
- [ ] L'import d'un ShapeFile test fonctionne
- [ ] La carte affiche correctement les couches

---

## Ressources complémentaires

- [Documentation Docker](https://docs.docker.com/)
- [Documentation Django](https://docs.djangoproject.com/)
- [Documentation PostGIS](https://postgis.net/documentation/)
- [Documentation Vite](https://vitejs.dev/guide/)

---

## Support

En cas de problème persistant :

1. Consulter les logs : `make logs`
2. Vérifier les issues GitHub du projet
3. Contacter l'équipe de développement (voir [README.md](../README.md))
