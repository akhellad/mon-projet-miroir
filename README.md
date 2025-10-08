# Observatoire SDAEP Ardèche

**Plateforme web de visualisation et gestion des infrastructures d'eau potable du département de l'Ardèche**

---

## Contexte du projet

Le Département de l'Ardèche met à jour son **Schéma Directeur d'Alimentation en Eau Potable (SDAEP)**, initialement réalisé en 2015. Ce projet, piloté par NALDEO, vise à créer un observatoire web pour visualiser, gérer et suivre les infrastructures d'eau potable sur l'ensemble du territoire départemental.

**Périmètre :**
- 335 communes
- ~130 collectivités gestionnaires
- Durée du projet : 30 mois (octobre 2025 → avril 2028)

**Objectifs :**
- Centraliser les données eau potable (captages, conduites, qualité, débits, etc.)
- Fournir une interface cartographique interactive
- Générer des fiches de synthèse par collectivité (UGE/UDI)
- Faciliter le suivi et la mise à jour du schéma directeur

---

## Architecture technique

### Stack technologique

**Backend**
- Django 5.2 + GeoDjango
- Django REST Framework 3.16
- PostgreSQL 16 + PostGIS 3.4
- Python 3.x

**Frontend**
- React 19 + Vite
- Leaflet.js (cartographie)
- Axios (API client)


**Outils annexes**
- WeasyPrint (génération PDF)
- Matplotlib (graphiques)
- QGIS (projets .qgz à livrer)

### Données géospatiales

- **Système de coordonnées** : Lambert 93 (EPSG:2154)
- **Types de géométries** : Points (captages), LineString (conduites), Polygon (communes, zones)
- **Sources** : SISPEA, données historiques 2015, questionnaires collectivités, fonds IGN

---

## Démarrage rapide

### Prérequis

- Docker & Docker Compose
- Make (optionnel, pour les commandes simplifiées)

### Installation

1. **Cloner le dépôt**
   ```bash
   git clone <url-du-repo>
   cd sdaep-observatoire
   ```

2. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec vos valeurs (mots de passe, secrets, etc.)
   ```

3. **Démarrer les services**
   ```bash
   make build
   make up
   ```

   Ou sans Make :
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **Appliquer les migrations et créer un superuser**
   ```bash
   make migrate
   make createsuperuser
   ```

5. **Accéder à l'application**
   - Frontend : [http://localhost:5173](http://localhost:5173)
   - Backend API : [http://localhost:8000/api](http://localhost:8000/api)
   - Admin Django : [http://localhost:8000/admin](http://localhost:8000/admin)

---

## Commandes utiles

Le projet inclut un `Makefile` pour simplifier les opérations courantes :

```bash
make help              # Afficher toutes les commandes disponibles
make up                # Démarrer les services
make down              # Arrêter les services
make logs              # Voir les logs
make migrate           # Exécuter les migrations Django
make makemigrations    # Créer de nouvelles migrations
make shell             # Ouvrir un shell Django
make db-shell          # Ouvrir un shell PostgreSQL
make test              # Lancer les tests
make rebuild           # Reconstruire et redémarrer
```

---

## Structure du projet

```
sdaep-observatoire/
├── backend/              # Application Django
│   ├── config/          # Configuration Django
│   ├── observatoire/    # App principale (models, views, serializers)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # Application React
│   ├── src/
│   │   ├── components/  # Composants UI
│   │   └── contexts/    # Contexts React
│   ├── Dockerfile
│   └── package.json
├── docs/                # Documentation technique
│   ├── ARCHITECTURE.md
│   ├── INSTALLATION.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
├── docker-compose.yml   # Orchestration des services
├── Makefile            # Commandes simplifiées
└── .env.example        # Template de configuration
```

---

## Fonctionnalités principales

### Cartographie interactive
- Affichage des couches SIG (captages, conduites, communes, UGE)
- Fonds de carte IGN (SCAN 25, BD ORTHO)
- Outils de mesure et dessin
- Filtres et recherche spatiale
- Export des données (GeoJSON, ShapeFile)

### Gestion des données
- Import/export de couches géographiques
- Gestion des propriétés attributaires
- Styles personnalisables par couche
- Interface d'administration Django

### Génération de fiches de synthèse
- Fiches par UGE (Unité de Gestion de l'Eau)
- Fiches par UDI (Unité de Distribution)
- Export PDF avec graphiques et cartes
- Données : population, ressources, qualité eau, bilans

---

## Documentation

Pour aller plus loin, consultez la documentation technique dans le dossier [`docs/`](docs/) :

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architecture détaillée et schémas
- **[INSTALLATION.md](docs/INSTALLATION.md)** - Guide d'installation complet
- **[API.md](docs/API.md)** - Documentation des endpoints REST
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Guide de développement et bonnes pratiques

---

## Sécurité

- Mots de passe : minimum 20 caractères
- Principe du "besoin d'en connaître" pour les accès
- Secret Detection activé dans la CI/CD GitLab
- Variables sensibles dans `.env` (jamais commitées)

---

## Livrables du projet

1. **Base de données PostgreSQL/PostGIS** - Dump complet avec toutes les données
2. **Application web** - Interface React + API Django en production
3. **Projets QGIS** - Fichiers .qgz connectés à la base
4. **Documentation** - Dossier d'Architecture Technique, catalogue de données, guide utilisateur
5. **Formation** - Sessions pour les agents du Département
6. **Conteneur Docker** - Pour déploiement sur serveurs du Département

---

## Support & Contact

Pour toute question sur le projet :
- **Développeurs** : Khelladi Djalil, Ploton Mathis
- **Entreprise** : NALDEO
- **Client** : Département de l'Ardèche

---

## Licence

Ce projet est développé dans le cadre d'un marché public pour le Département de l'Ardèche.
Propriété : Département de l'Ardèche - Tous droits réservés.
