# Architecture technique - Observatoire SDAEP

## Vue d'ensemble

L'Observatoire SDAEP est une application web full-stack orientée données géospatiales, composée de trois services principaux orchestrés via Docker Compose.

```
┌─────────────────────────────────────────────────────────────┐
│                         UTILISATEUR                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   Frontend     │
                    │   React +      │
                    │   Leaflet      │
                    │   Port: 5173   │
                    └───────┬────────┘
                            │ HTTP/REST
                    ┌───────▼────────┐
                    │   Backend      │
                    │   Django +     │
                    │   DRF + GIS    │
                    │   Port: 8000   │
                    └───────┬────────┘
                            │ SQL/PostGIS
                    ┌───────▼────────┐
                    │   Database     │
                    │   PostgreSQL + │
                    │   PostGIS      │
                    │   Port: 5432   │
                    └────────────────┘
```

---

## Stack technique détaillée

### 🎨 Frontend

**Framework & UI**
- **React 19.1.1** - Framework UI moderne avec hooks
- **Vite 7.1** - Build tool ultra-rapide
- **Axios 1.12** - Client HTTP pour les appels API

**Cartographie**
- **Leaflet.js 1.9.4** - Bibliothèque cartographique open-source
- **React-Leaflet 5.0** - Intégration React pour Leaflet
- **Leaflet-Draw** - Outils de dessin et mesure
- **Proj4 2.12** - Projections cartographiques (Lambert 93 ↔ WGS84)
- **Turf.js 7.1** - Calculs géospatiaux client-side

**Visualisation de données**
- **Recharts 2.13** - Graphiques et tableaux de bord

**Structure des composants**
```
src/
├── App.jsx                      # Point d'entrée
├── contexts/
│   └── LayerContext.jsx         # Gestion état des couches
├── components/
    ├── MapToolbar.jsx           # Barre d'outils cartographiques
    ├── LayerManager.jsx         # Gestionnaire de couches
    ├── Sidebar.jsx              # Panneau latéral
    ├── Dashboard.jsx            # Tableaux de bord
    ├── Export.jsx               # Module d'export
    ├── GeoJSONLayer.jsx         # Rendu des couches GeoJSON
    └── MouseCoordinates.jsx     # Affichage coordonnées
```

---

### ⚙️ Backend

**Framework principal**
- **Django 5.2.6** - Framework web Python
- **GeoDjango** - Extension pour données géospatiales
- **Django REST Framework 3.16** - API REST
- **Django REST Framework GIS 1.2** - Sérialisation GeoJSON

**Base de données**
- **psycopg2-binary 2.9.10** - Adaptateur PostgreSQL pour Python
- **Django Filter 25.1** - Filtres avancés pour API

**Géospatial & Export**
- **WeasyPrint 62.3** - Génération PDF (fiches de synthèse)
- **Matplotlib 3.9.4** - Génération de graphiques pour PDF
- **Requests** - Appels HTTP externes (fonds IGN, API tierces)

**Configuration**
- **Python-decouple 3.8** - Gestion variables d'environnement

**Modèle de données principal**

```python
# backend/observatoire/models.py

Layer (Couche géographique)
├── id
├── name                  # Nom de la couche
├── description
├── geometry_type         # Point, LineString, Polygon, Multi*
├── identifier_field      # Champ identifiant (ex: 'code_insee')
├── style_*              # Propriétés de style (couleur, opacité, épaisseur)
├── srid                 # Système de coordonnées (défaut: 2154)
├── visible              # Visibilité par défaut
└── features ───────────► Feature (Entités géographiques)
                          ├── id
                          ├── layer_id (FK)
                          ├── geom (GeometryField)
                          └── properties (JSON)
```

---

### 🗄️ Base de données

**PostgreSQL 16 + PostGIS 3.4**

**Extensions activées**
- `postgis` - Types géométriques et fonctions spatiales
- `postgis_topology` - Gestion topologique
- `postgis_raster` - Support raster (futur)

**Système de coordonnées**
- **SRID de stockage** : 2154 (Lambert 93 - projection officielle française)
- **SRID d'export** : 4326 (WGS84 - standard web/Leaflet)
- **Transformation automatique** via `ST_Transform(geom, 4326)` dans les requêtes

**Optimisations**
- Index spatiaux GIST sur les géométries
- Requêtes SQL directes pour les couches >10 000 features
- Utilisation de `json_build_object` pour génération GeoJSON côté BDD

**Tables principales**
```sql
-- Couches géographiques
layers
  ├── Métadonnées (nom, description, type de géométrie)
  ├── Configuration de style
  └── Paramètres de référencement spatial

-- Entités géographiques
features
  ├── layer_id (FK vers layers)
  ├── geom (GEOMETRY) avec index GIST
  └── properties (JSONB) pour attributs dynamiques
```

---

## Architecture logicielle

### Pattern MVC

```
┌──────────────────────────────────────────────────────┐
│                     FRONTEND                          │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   View     │  │  Context    │  │  Components  │  │
│  │  (React)   │◄─┤ (LayerCtx)  │◄─┤   (UI)       │  │
│  └────────────┘  └─────────────┘  └──────────────┘  │
└───────────────────────┬──────────────────────────────┘
                        │ REST API (JSON/GeoJSON)
┌───────────────────────▼──────────────────────────────┐
│                     BACKEND                           │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   Model    │  │    View     │  │  Serializer  │  │
│  │  (Django)  │◄─┤  (ViewSet)  │◄─┤    (DRF)     │  │
│  └─────┬──────┘  └─────────────┘  └──────────────┘  │
└────────┼─────────────────────────────────────────────┘
         │ ORM (SQL)
┌────────▼─────────────────────────────────────────────┐
│                    DATABASE                           │
│         PostgreSQL + PostGIS (Géométries)             │
└───────────────────────────────────────────────────────┘
```

### API REST - Endpoints principaux

| Méthode | Endpoint                            | Description                          |
|---------|-------------------------------------|--------------------------------------|
| GET     | `/api/layers/`                      | Liste toutes les couches             |
| POST    | `/api/layers/`                      | Créer une nouvelle couche            |
| GET     | `/api/layers/{id}/`                 | Détails d'une couche                 |
| PUT     | `/api/layers/{id}/`                 | Mettre à jour une couche             |
| DELETE  | `/api/layers/{id}/`                 | Supprimer une couche                 |
| GET     | `/api/layers/{id}/geojson/`         | Features au format GeoJSON           |
| GET     | `/api/layers/{id}/properties/`      | Propriétés sans géométries (stats)   |
| POST    | `/api/upload-shapefile/`            | Import ShapeFile → PostGIS           |
| GET     | `/api/export/commune/{code_insee}/` | Export PDF fiche de synthèse         |
| GET     | `/api/preview/commune/{code_insee}/`| Prévisualisation HTML de la fiche    |

**Format GeoJSON retourné**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 1,
      "geometry": {
        "type": "Point",
        "coordinates": [4.8357, 44.7354]
      },
      "properties": {
        "nom": "Captage des Sources",
        "commune": "Privas",
        "debit_max": 150
      }
    }
  ]
}
```

---

## Flux de données

### 1. Chargement d'une carte

```
User clique sur une couche
         │
         ▼
Frontend (LayerContext)
    ├── GET /api/layers/{id}/geojson/
    │        │
    │        ▼
    │   Backend (views.layer_geojson)
    │        ├── Si >10k features → requête SQL optimisée
    │        └── Sinon → serializer DRF standard
    │             │
    │             ▼
    │        PostGIS: ST_AsGeoJSON(ST_Transform(geom, 4326))
    │             │
    │        ◄────┘
    │   GeoJSON
    ▼
GeoJSONLayer (Leaflet)
    └── Affichage sur la carte
```

### 2. Import d'un ShapeFile

```
User upload un .zip (ShapeFile)
         │
         ▼
Frontend: FormData + POST /api/upload-shapefile/
         │
         ▼
Backend (shapefile_importer.py)
    ├── 1. Décompression du ZIP
    ├── 2. Lecture avec GDAL/OGR
    ├── 3. Transformation SRID → 2154
    ├── 4. Création Layer
    └── 5. Bulk insert Features
         │
         ▼
PostGIS: INSERT INTO features (geom, properties, layer_id)
         │
         ◄─── Succès
         │
Frontend: Refresh liste des couches
```

### 3. Génération de fiche PDF

```
User demande fiche commune (code INSEE)
         │
         ▼
Frontend: GET /api/export/commune/07186/
         │
         ▼
Backend (views.export_commune_pdf)
    ├── 1. Récupération données commune (PostGIS)
    ├── 2. Génération graphiques (Matplotlib → base64)
    ├── 3. Rendu template HTML (Django templates)
    └── 4. Conversion HTML → PDF (WeasyPrint)
         │
         ▼
User télécharge fiche.pdf
```

---

## Containerisation Docker

### Services définis

**docker-compose.yml**
```yaml
services:
  db:           # PostgreSQL + PostGIS
  backend:      # Django (port 8000)
  frontend:     # React + Vite (port 5173)
```

**Volumes persistants**
- `postgres_data` : Données PostgreSQL
- `./backend:/app` : Hot-reload Django
- `./frontend:/app` : Hot-reload React

**Healthcheck**
- Le service `backend` attend que `db` soit opérationnel
- Le service `frontend` attend le démarrage du `backend`

---

## Sécurité

### Variables d'environnement sensibles

Toutes les configurations critiques sont externalisées dans `.env` :

```bash
DB_PASSWORD           # Mot de passe PostgreSQL (min 20 caractères)
SECRET_KEY            # Clé secrète Django (min 50 caractères)
SUPERUSER_PASSWORD    # Mot de passe admin
OIDC_RP_CLIENT_SECRET # Secret OAuth (futur)
```

### Mesures de sécurité

- **Secret Detection** activé dans GitLab CI
- `.env` dans `.gitignore` (jamais committé)
- Template `.env.example` pour onboarding
- CORS restreint aux origines autorisées
- `ALLOWED_HOSTS` configuré pour production

### Principe du "besoin d'en connaître"

Les accès aux données seront segmentés par rôles :
- **Admin** : accès complet
- **Gestionnaire** : modification couches spécifiques
- **Lecteur** : consultation uniquement

---

## Performance

### Optimisations appliquées

**Backend**
- Requêtes SQL directes pour couches >10k features
- `json_build_object` pour génération GeoJSON côté BDD
- Index GIST sur géométries
- Sérialisation sans géométries pour endpoint `/properties/` (stats)

**Frontend**
- Code-splitting avec Vite
- Lazy loading des composants
- Gestion du state avec Context API (évite prop drilling)
- Debouncing sur les interactions map (zoom, pan)

**Base de données**
- Connection pooling PostgreSQL
- VACUUM automatique configuré
- ANALYZE régulier pour optimiser le planner

---

## Évolutions prévues

### Palier B (court terme)
- Module dashboard avec Recharts
- Export multi-formats (ShapeFile, GeoPackage)
- Système de recherche full-text
- Authentification OIDC (SSO)

### Palier C (moyen terme)
- Module de simulation (scénarios 2035, 2050)
- Intégration flux WMS/WFS IGN
- Versioning des données
- API GraphQL (alternative REST)

### Production
- Reverse proxy Nginx
- Serveur WSGI Gunicorn
- SSL/TLS
- Monitoring (logs, métriques)
- Backup automatisé BDD

---

## Dépendances externes

### Fonds de carte IGN

**Plan** : Intégrer les fonds IGN via API Géoportail
- SCAN 25 (cartes topographiques)
- BD ORTHO (photographies aériennes)
- BD TOPO (référentiel géographique)

**Authentification** : Clé API IGN (à obtenir)

### SISPEA

**Système d'Information sur les Services Publics d'Eau et d'Assainissement**
- Import périodique des données nationales
- Réconciliation avec données locales
- Endpoint : `https://www.services.eaufrance.fr/sispea`

---

## Standards et conformité

### Formats supportés

**Import**
- ShapeFile (.shp + .dbf + .shx + .prj)
- GeoJSON (.geojson)
- GeoPackage (.gpkg) - à venir

**Export**
- GeoJSON (standard web)
- PDF (fiches de synthèse)
- ShapeFile (futur)

### Normes géospatiales

- **OGC** : Open Geospatial Consortium
  - Simple Features (géométries)
  - WMS/WFS (futur)
- **INSPIRE** : Directive européenne sur l'interopérabilité
- **EPSG** : Registre des systèmes de coordonnées

---

## Diagramme de déploiement (Production)

```
┌─────────────────────────────────────────────────┐
│          Serveurs Département Ardèche            │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │            Nginx (reverse proxy)          │  │
│  │            Port 80/443 (HTTPS)            │  │
│  └────────────┬──────────────────────────────┘  │
│               │                                  │
│       ┌───────┴────────┐                        │
│       │                │                        │
│  ┌────▼─────┐    ┌────▼──────┐                 │
│  │ Frontend │    │  Backend  │                  │
│  │  (Vite   │    │  (Django  │                  │
│  │  build)  │    │ +Gunicorn)│                  │
│  └──────────┘    └─────┬─────┘                  │
│                        │                         │
│                  ┌─────▼──────┐                  │
│                  │ PostgreSQL │                  │
│                  │  + PostGIS │                  │
│                  └────────────┘                  │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Déploiement via Docker**
- Image Docker custom livrée au Département
- Docker Compose pour orchestration
- Volumes persistants pour données PostgreSQL
- Configuration via variables d'environnement

---

## Références techniques

- [Django Documentation](https://docs.djangoproject.com/)
- [GeoDjango](https://docs.djangoproject.com/fr/5.0/ref/contrib/gis/)
- [PostGIS](https://postgis.net/documentation/)
- [Leaflet.js](https://leafletjs.com/)
- [React](https://react.dev/)
- [Docker Compose](https://docs.docker.com/compose/)
