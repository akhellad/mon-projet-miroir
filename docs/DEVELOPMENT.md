# Guide de développement - Observatoire SDAEP

Ce guide présente les bonnes pratiques de développement, la structure du code, et les workflows recommandés pour contribuer au projet.

---

## Table des matières

- [Setup développeur](#setup-développeur)
- [Structure du projet](#structure-du-projet)
- [Workflow Git](#workflow-git)
- [Backend Django](#backend-django)
- [Frontend React](#frontend-react)
- [Base de données](#base-de-données)
- [Tests](#tests)
- [Bonnes pratiques](#bonnes-pratiques)
- [Debugging](#debugging)

---

## Setup développeur

### Prérequis

Voir [INSTALLATION.md](INSTALLATION.md) pour l'installation complète.

**Résumé rapide :**

```bash
# Cloner le dépôt
git clone https://github.com/votre-organisation/sdaep-observatoire.git
cd sdaep-observatoire

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Démarrer les services
make build
make up
make migrate
make createsuperuser

# Accéder à l'application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

### Outils recommandés

**Éditeur de code**
- **VSCode** (recommandé) avec extensions :
  - Python (Microsoft)
  - ESLint
  - Prettier
  - Volar (Vue/React)
  - Docker
  - GitLens

**Outils CLI**
- **httpie** ou **curl** pour tester l'API
- **psql** pour la base de données
- **QGIS** pour visualiser les données géospatiales

---

## Structure du projet

```
sdaep-observatoire/
├── backend/                    # Application Django
│   ├── config/                # Configuration Django
│   │   ├── settings.py       # Paramètres (BDD, CORS, etc.)
│   │   ├── urls.py           # Routes principales
│   │   └── wsgi.py           # Point d'entrée WSGI
│   ├── observatoire/         # App principale
│   │   ├── models.py         # Modèles Django (Layer, Feature)
│   │   ├── views.py          # ViewSets et API views
│   │   ├── serializers.py    # Sérialisation JSON/GeoJSON
│   │   ├── admin.py          # Interface d'administration
│   │   ├── charts.py         # Génération de graphiques
│   │   ├── shapefile_importer.py  # Import ShapeFile
│   │   └── migrations/       # Migrations de BDD
│   ├── manage.py             # CLI Django
│   ├── requirements.txt      # Dépendances Python
│   └── Dockerfile            # Image Docker backend
│
├── frontend/                  # Application React
│   ├── src/
│   │   ├── App.jsx           # Composant racine
│   │   ├── contexts/         # Contexts React (état global)
│   │   │   └── LayerContext.jsx
│   │   ├── components/       # Composants UI
│   │   │   ├── MapToolbar.jsx
│   │   │   ├── LayerManager.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Export.jsx
│   │   │   └── GeoJSONLayer.jsx
│   │   └── main.jsx          # Point d'entrée
│   ├── package.json          # Dépendances npm
│   ├── vite.config.js        # Configuration Vite
│   └── Dockerfile            # Image Docker frontend
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md
│   ├── INSTALLATION.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md (ce fichier)
│
├── docker-compose.yml         # Orchestration dev
├── Makefile                   # Commandes simplifiées
├── .env.example               # Template de configuration
├── .gitignore                 # Fichiers ignorés par Git
└── README.md                  # Documentation principale
```

---

## Workflow Git

### Branches

| Branche   | Usage                                  |
|-----------|----------------------------------------|
| `main`    | Code stable en production              |
| `dev`     | Développement en cours                 |
| `feature/*` | Nouvelles fonctionnalités (ex: `feature/export-pdf`) |
| `fix/*`   | Corrections de bugs (ex: `fix/cors-issue`) |

### Workflow recommandé

**1. Créer une branche pour chaque tâche**

```bash
# Se positionner sur dev
git checkout dev
git pull origin dev

# Créer une branche feature
git checkout -b feature/ajout-dashboard

# Travailler sur la fonctionnalité
# ...

# Commit réguliers
git add .
git commit -m "feat: ajout du composant Dashboard avec graphiques population"

# Pousser vers le dépôt distant
git push origin feature/ajout-dashboard
```

**2. Conventions de commit**

Utiliser le format **Conventional Commits** :

```
<type>(<scope>): <description>

[body optionnel]

[footer optionnel]
```

**Types :**
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage, points-virgules manquants, etc.
- `refactor`: Refactoring de code
- `test`: Ajout de tests
- `chore`: Tâches de maintenance (dépendances, config)

**Exemples :**

```bash
git commit -m "feat(api): ajout endpoint /api/export/shapefile/"
git commit -m "fix(frontend): correction affichage couches vides"
git commit -m "docs: mise à jour README avec nouvelles commandes"
git commit -m "refactor(backend): optimisation requête SQL pour couches >10k features"
```

---

## Backend Django

### Structure du code

**models.py** : Définition des modèles de données

```python
from django.contrib.gis.db import models

class Layer(models.Model):
    """Couche géographique"""
    name = models.CharField(max_length=200)
    geometry_type = models.CharField(max_length=50)
    # ...

class Feature(models.Model):
    """Entité géographique"""
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name='features')
    geom = models.GeometryField(srid=2154)
    properties = models.JSONField()
```

**serializers.py** : Conversion modèles → JSON/GeoJSON

```python
from rest_framework_gis.serializers import GeoFeatureModelSerializer

class FeatureSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Feature
        geo_field = "geom"
        fields = ['id']
```

**views.py** : Endpoints API

```python
from rest_framework import viewsets
from rest_framework.decorators import api_view

class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer

@api_view(['GET'])
def layer_geojson(request, layer_id):
    # ...
    return Response(geojson_data)
```

### Créer une migration

Après modification d'un modèle :

```bash
# Créer la migration
make makemigrations

# Appliquer la migration
make migrate

# Vérifier l'état des migrations
docker compose exec backend python manage.py showmigrations
```

**Nommage des migrations :**

```bash
# Migration automatique
python manage.py makemigrations

# Migration avec nom explicite
python manage.py makemigrations observatoire --name ajout_champ_source_externe
```

### Ajouter un endpoint API

**1. Créer la fonction dans `views.py` :**

```python
@api_view(['GET'])
def layer_statistics(request, layer_id):
    """Retourne les statistiques d'une couche"""
    try:
        layer = Layer.objects.get(id=layer_id)
    except Layer.DoesNotExist:
        return Response({'error': 'Couche non trouvée'}, status=404)

    stats = {
        'total_features': layer.features.count(),
        'geometry_type': layer.geometry_type,
        'srid': layer.srid
    }
    return Response(stats)
```

**2. Ajouter la route dans `urls.py` :**

```python
from observatoire.views import layer_statistics

urlpatterns = [
    # ...
    path('api/layers/<int:layer_id>/stats/', layer_statistics, name='layer_statistics'),
]
```

**3. Tester l'endpoint :**

```bash
curl http://localhost:8000/api/layers/1/stats/
```

### Utiliser le shell Django

```bash
# Ouvrir un shell Python avec accès aux modèles
make shell

# Ou
docker compose exec backend python manage.py shell
```

**Exemples d'utilisation :**

```python
# Importer les modèles
from observatoire.models import Layer, Feature

# Lister toutes les couches
layers = Layer.objects.all()
for layer in layers:
    print(f"{layer.id}: {layer.name} ({layer.features.count()} features)")

# Récupérer une couche spécifique
communes = Layer.objects.get(name='Communes')

# Compter les features
print(communes.features.count())

# Filtrer les features par propriété
privas_features = communes.features.filter(properties__nom='Privas')

# Exécuter une requête SQL brute
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT PostGIS_Version();")
    print(cursor.fetchone())
```

---

## Frontend React

### Structure des composants

**Composant fonctionnel avec hooks :**

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const LayerList = () => {
  const [layers, setLayers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLayers = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/layers/');
        setLayers(response.data);
      } catch (error) {
        console.error('Erreur chargement couches:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLayers();
  }, []);

  if (loading) return <div>Chargement...</div>;

  return (
    <ul>
      {layers.map(layer => (
        <li key={layer.id}>{layer.name} ({layer.feature_count} features)</li>
      ))}
    </ul>
  );
};

export default LayerList;
```

### Context API (gestion d'état)

**LayerContext.jsx** :

```javascript
import React, { createContext, useState, useContext } from 'react';

const LayerContext = createContext();

export const LayerProvider = ({ children }) => {
  const [selectedLayers, setSelectedLayers] = useState([]);

  const toggleLayer = (layerId) => {
    setSelectedLayers(prev =>
      prev.includes(layerId)
        ? prev.filter(id => id !== layerId)
        : [...prev, layerId]
    );
  };

  return (
    <LayerContext.Provider value={{ selectedLayers, toggleLayer }}>
      {children}
    </LayerContext.Provider>
  );
};

export const useLayerContext = () => useContext(LayerContext);
```

**Utilisation dans un composant :**

```javascript
import { useLayerContext } from '../contexts/LayerContext';

const LayerToggle = ({ layer }) => {
  const { selectedLayers, toggleLayer } = useLayerContext();
  const isSelected = selectedLayers.includes(layer.id);

  return (
    <button onClick={() => toggleLayer(layer.id)}>
      {isSelected ? '✓' : '○'} {layer.name}
    </button>
  );
};
```

### Intégration Leaflet

```javascript
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { useEffect, useState } from 'react';
import axios from 'axios';

const Map = ({ layerId }) => {
  const [geojson, setGeojson] = useState(null);

  useEffect(() => {
    const loadLayer = async () => {
      const { data } = await axios.get(
        `http://localhost:8000/api/layers/${layerId}/geojson/`
      );
      setGeojson(data);
    };

    if (layerId) loadLayer();
  }, [layerId]);

  return (
    <MapContainer center={[44.73, 4.60]} zoom={10} style={{ height: '600px' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {geojson && (
        <GeoJSON
          data={geojson}
          style={{ color: '#3388ff', weight: 2 }}
          onEachFeature={(feature, layer) => {
            layer.bindPopup(`<strong>${feature.properties.nom}</strong>`);
          }}
        />
      )}
    </MapContainer>
  );
};
```
---

## Base de données

### Commandes PostgreSQL utiles

```bash
# Ouvrir un shell PostgreSQL
make db-shell

# Lister les tables
\dt

# Décrire une table
\d layers
\d features

# Voir les index
\di

# Exécuter une requête
SELECT name, geometry_type, feature_count FROM layers;

# Vérifier PostGIS
SELECT PostGIS_Version();

# Compter les features par couche
SELECT l.name, COUNT(f.id) as nb_features
FROM layers l
LEFT JOIN features f ON f.layer_id = l.id
GROUP BY l.name;
```

### Requêtes spatiales PostGIS

```sql
-- Trouver tous les captages dans un rayon de 5km autour de Privas (coords Lambert 93)
SELECT f.id, f.properties->>'nom' as nom,
       ST_Distance(f.geom, ST_SetSRID(ST_MakePoint(784000, 6422000), 2154)) as distance_m
FROM features f
WHERE f.layer_id = (SELECT id FROM layers WHERE name = 'Captages')
  AND ST_DWithin(f.geom, ST_SetSRID(ST_MakePoint(784000, 6422000), 2154), 5000)
ORDER BY distance_m;

-- Calculer la surface d'une commune (en ha)
SELECT properties->>'nom' as commune,
       ST_Area(geom) / 10000 as surface_ha
FROM features
WHERE layer_id = (SELECT id FROM layers WHERE name = 'Communes')
  AND properties->>'code_insee' = '07186';

-- Intersection entre deux couches (captages dans une commune)
SELECT c.properties->>'nom' as captage, co.properties->>'nom' as commune
FROM features c, features co
WHERE c.layer_id = (SELECT id FROM layers WHERE name = 'Captages')
  AND co.layer_id = (SELECT id FROM layers WHERE name = 'Communes')
  AND ST_Within(c.geom, co.geom);
```

---

## Tests

### Backend (Django)

**Créer un fichier `observatoire/tests.py` :**

```python
from django.test import TestCase
from rest_framework.test import APIClient
from observatoire.models import Layer

class LayerAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.layer = Layer.objects.create(
            name='Test Layer',
            geometry_type='Point',
            srid=2154
        )

    def test_list_layers(self):
        response = self.client.get('/api/layers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Layer')

    def test_create_layer(self):
        data = {
            'name': 'New Layer',
            'geometry_type': 'Polygon',
            'srid': 2154
        }
        response = self.client.post('/api/layers/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Layer.objects.count(), 2)
```

**Lancer les tests :**

```bash
make test

# Ou
docker compose exec backend python manage.py test
```

### Frontend (Jest - à configurer)

```bash
cd frontend
npm install --save-dev jest @testing-library/react

# Créer un test
# src/components/__tests__/LayerList.test.jsx

# Lancer les tests
npm test
```

---

## Bonnes pratiques

### Code

**Backend (Python/Django)**
- Suivre [PEP 8](https://peps.python.org/pep-0008/)
- Docstrings pour toutes les fonctions/classes
- Type hints quand possible
- Éviter les requêtes N+1 (utiliser `select_related`, `prefetch_related`)

**Frontend (JavaScript/React)**
- Utiliser des composants fonctionnels + hooks
- Éviter le prop drilling (utiliser Context API ou état global)
- Nommage explicite des variables
- Commentaires pour la logique complexe

### Sécurité

- **Jamais** committer le fichier `.env`
- **Jamais** hardcoder des secrets dans le code
- Toujours valider les inputs utilisateur
- Utiliser HTTPS en production
- Activer CORS uniquement pour les origines autorisées

### Performance

- Optimiser les requêtes SQL (utiliser `django-debug-toolbar` en dev)
- Lazy loading pour les couches volumineuses
- Compression gzip pour les exports
- Index sur les champs fréquemment filtrés

---

## Debugging

### Backend

**Utiliser django-debug-toolbar :**

```bash
# Installer
pip install django-debug-toolbar

# Ajouter dans settings.py (mode dev uniquement)
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

**Logs Django :**

```bash
# Voir les logs backend
make logs-backend

# Activer le mode verbeux dans settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'DEBUG'},
}
```

### Frontend

**Utiliser React DevTools (extension navigateur)**

**Console navigateur :**

```javascript
// Ajouter des logs de debug
console.log('Layers loaded:', layers);

// Breakpoints dans le code
debugger;
```

### Base de données

```sql
-- Afficher les requêtes lentes (>100ms)
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC;

-- Analyser une requête
EXPLAIN ANALYZE
SELECT * FROM features WHERE layer_id = 1;
```

---

## Ressources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://react.dev/)
- [Leaflet.js](https://leafletjs.com/)
- [PostGIS](https://postgis.net/documentation/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)

---

## Support

Pour toute question sur le développement, consulter la documentation ou contacter l'équipe (voir [README.md](../README.md)).
