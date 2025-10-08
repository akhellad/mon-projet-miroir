# Documentation API - Observatoire SDAEP

L'API REST de l'Observatoire SDAEP est construite avec **Django REST Framework** et expose des endpoints pour gérer les couches géographiques, les entités spatiales, et générer des exports.

**Base URL** : `http://localhost:8000/api/` (développement)

---

## Table des matières

- [Authentication](#authentication)
- [Formats de réponse](#formats-de-réponse)
- [Endpoints](#endpoints)
  - [Layers (Couches)](#layers-couches)
  - [Features (Entités)](#features-entités)
  - [Import](#import)
  - [Export](#export)
- [Codes d'erreur](#codes-derreur)
- [Exemples d'utilisation](#exemples-dutilisation)

---

## Authentication

**Développement** : Pas d'authentification requise (mode DEBUG)

**Production** : Authentification par session Django ou Token (à configurer)

```bash
# Authentification future (Token)
curl -H "Authorization: Token YOUR_TOKEN_HERE" \
  http://localhost:8000/api/layers/
```

---

## Formats de réponse

L'API retourne toujours du JSON, et du **GeoJSON** pour les données géographiques.

**Succès** : Code HTTP 200, 201, ou 204
```json
{
  "id": 1,
  "name": "Communes Ardèche",
  "geometry_type": "Polygon"
}
```

**Erreur** : Code HTTP 400, 404, ou 500
```json
{
  "error": "Couche non trouvée"
}
```

---

## Endpoints

### Layers (Couches)

Les couches représentent des groupes d'entités géographiques (communes, captages, conduites, etc.).

#### **GET** `/api/layers/`

Liste toutes les couches géographiques.

**Paramètres** : Aucun

**Réponse** :
```json
[
  {
    "id": 1,
    "name": "Communes Ardèche",
    "description": "Limites administratives des communes",
    "geometry_type": "Polygon",
    "identifier_field": "code_insee",
    "style_color": "#3388ff",
    "style_weight": 2,
    "style_opacity": 0.8,
    "style_fill_opacity": 0.2,
    "source_file": "communes_ardeche.shp",
    "srid": 2154,
    "visible": true,
    "created_at": "2025-10-01T10:30:00Z",
    "updated_at": "2025-10-05T14:20:00Z",
    "feature_count": 335
  },
  {
    "id": 2,
    "name": "Captages AEP",
    "description": "Points de captage d'eau potable",
    "geometry_type": "Point",
    "identifier_field": "code_bss",
    "style_color": "#00ff00",
    "style_weight": 3,
    "style_opacity": 1.0,
    "style_fill_opacity": 0.6,
    "source_file": "captages.geojson",
    "srid": 2154,
    "visible": true,
    "created_at": "2025-10-02T09:15:00Z",
    "updated_at": "2025-10-02T09:15:00Z",
    "feature_count": 427
  }
]
```

**Exemple cURL** :
```bash
curl http://localhost:8000/api/layers/
```

---

#### **POST** `/api/layers/`

Créer une nouvelle couche.

**Body (JSON)** :
```json
{
  "name": "Conduites principales",
  "description": "Réseau de conduites principales AEP",
  "geometry_type": "LineString",
  "identifier_field": "id_conduite",
  "style_color": "#ff0000",
  "style_weight": 3,
  "style_opacity": 0.9,
  "style_fill_opacity": 0.0,
  "srid": 2154,
  "visible": true
}
```

**Réponse (201 Created)** :
```json
{
  "id": 3,
  "name": "Conduites principales",
  "description": "Réseau de conduites principales AEP",
  "geometry_type": "LineString",
  "identifier_field": "id_conduite",
  "style_color": "#ff0000",
  "style_weight": 3,
  "style_opacity": 0.9,
  "style_fill_opacity": 0.0,
  "source_file": null,
  "srid": 2154,
  "visible": true,
  "created_at": "2025-10-08T12:00:00Z",
  "updated_at": "2025-10-08T12:00:00Z",
  "feature_count": 0
}
```

**Exemple cURL** :
```bash
curl -X POST http://localhost:8000/api/layers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conduites principales",
    "geometry_type": "LineString",
    "style_color": "#ff0000"
  }'
```

---

#### **GET** `/api/layers/{id}/`

Récupérer les détails d'une couche spécifique.

**Paramètres** :
- `id` (int, path) : ID de la couche

**Réponse (200 OK)** :
```json
{
  "id": 1,
  "name": "Communes Ardèche",
  "description": "Limites administratives des communes",
  "geometry_type": "Polygon",
  "identifier_field": "code_insee",
  "style_color": "#3388ff",
  "style_weight": 2,
  "style_opacity": 0.8,
  "style_fill_opacity": 0.2,
  "source_file": "communes_ardeche.shp",
  "srid": 2154,
  "visible": true,
  "created_at": "2025-10-01T10:30:00Z",
  "updated_at": "2025-10-05T14:20:00Z",
  "feature_count": 335
}
```

**Erreur (404 Not Found)** :
```json
{
  "detail": "Not found."
}
```

**Exemple curl** :
```bash
curl http://localhost:8000/api/layers/1/
```

---

#### **PUT** `/api/layers/{id}/`

Mettre à jour une couche existante.

**Paramètres** :
- `id` (int, path) : ID de la couche

**Body (JSON)** :
```json
{
  "name": "Communes Ardèche 2025",
  "description": "Limites administratives mises à jour",
  "visible": false
}
```

**Réponse (200 OK)** : Couche mise à jour

**Exemple cURL** :
```bash
curl -X PUT http://localhost:8000/api/layers/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Communes Ardèche 2025", "visible": false}'
```

---

#### **DELETE** `/api/layers/{id}/`

Supprimer une couche et toutes ses entités associées.

**Paramètres** :
- `id` (int, path) : ID de la couche

**Réponse (204 No Content)** : Suppression réussie

**Exemple cURL** :
```bash
curl -X DELETE http://localhost:8000/api/layers/1/
```

---

### Features (Entités)

Les entités sont les objets géographiques individuels d'une couche (une commune, un captage, etc.).

#### **GET** `/api/layers/{layer_id}/geojson/`

Récupérer toutes les entités d'une couche au format **GeoJSON**.

**Paramètres** :
- `layer_id` (int, path) : ID de la couche

**Réponse (200 OK)** :
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
        "code_bss": "07PRV001",
        "debit_max": 150,
        "qualite": "Bonne"
      }
    },
    {
      "type": "Feature",
      "id": 2,
      "geometry": {
        "type": "Point",
        "coordinates": [4.6012, 44.5598]
      },
      "properties": {
        "nom": "Captage du Moulin",
        "commune": "Aubenas",
        "code_bss": "07AUB002",
        "debit_max": 200,
        "qualite": "Moyenne"
      }
    }
  ]
}
```

**Notes importantes** :
- Les géométries sont automatiquement transformées en **WGS84 (EPSG:4326)** pour compatibilité Leaflet
- Pour les couches >10 000 features, une optimisation SQL est appliquée
- Les propriétés sont dynamiques (champ JSON `properties`)

**Exemple curl** :
```bash
curl http://localhost:8000/api/layers/2/geojson/
```

**Exemple JavaScript (Axios)** :
```javascript
import axios from 'axios';

const loadLayer = async (layerId) => {
  const response = await axios.get(`http://localhost:8000/api/layers/${layerId}/geojson/`);
  const geojson = response.data;

  // Ajouter à Leaflet
  L.geoJSON(geojson).addTo(map);
};

loadLayer(2);
```

---

#### **GET** `/api/layers/{layer_id}/properties/`

Récupérer uniquement les **propriétés** des entités (sans géométries).

**Utilité** : Optimisé pour les statistiques et tableaux de bord (évite le transfert de géométries lourdes).

**Paramètres** :
- `layer_id` (int, path) : ID de la couche

**Réponse (200 OK)** :
```json
{
  "type": "PropertiesCollection",
  "count": 427,
  "features": [
    {
      "id": 1,
      "properties": {
        "nom": "Captage des Sources",
        "commune": "Privas",
        "code_bss": "07PRV001",
        "debit_max": 150,
        "qualite": "Bonne"
      }
    },
    {
      "id": 2,
      "properties": {
        "nom": "Captage du Moulin",
        "commune": "Aubenas",
        "code_bss": "07AUB002",
        "debit_max": 200,
        "qualite": "Moyenne"
      }
    }
  ]
}
```

**Exemple curl** :
```bash
curl http://localhost:8000/api/layers/2/properties/
```

**Exemple JavaScript (calcul de statistiques)** :
```javascript
const stats = await axios.get('http://localhost:8000/api/layers/2/properties/');
const totalDebit = stats.data.features.reduce(
  (sum, f) => sum + (f.properties.debit_max || 0),
  0
);
console.log(`Débit total : ${totalDebit} m³/h`);
```

---

### Import

#### **POST** `/api/upload-shapefile/`

Importer un **ShapeFile** (compressé en ZIP) et créer une nouvelle couche.

**Content-Type** : `multipart/form-data`

**Paramètres (Form Data)** :
- `file` (file, required) : Fichier ZIP contenant `.shp`, `.dbf`, `.shx`, `.prj`
- `name` (string, optional) : Nom de la couche (défaut: "Nouvelle couche")
- `description` (string, optional) : Description
- `identifier_field` (string, optional) : Champ identifiant (défaut: "id")
- `style_color` (string, optional) : Couleur hex (défaut: "#3388ff")
- `force_srid` (int, optional) : Forcer le SRID si le `.prj` est manquant

**Réponse (201 Created)** :
```json
{
  "id": 4,
  "name": "Captages importés",
  "description": "Import depuis ShapeFile",
  "geometry_type": "Point",
  "identifier_field": "code_bss",
  "style_color": "#00ff00",
  "style_weight": 2,
  "style_opacity": 0.8,
  "style_fill_opacity": 0.2,
  "source_file": "captages.zip",
  "srid": 2154,
  "visible": true,
  "created_at": "2025-10-08T13:45:00Z",
  "updated_at": "2025-10-08T13:45:00Z",
  "feature_count": 150
}
```

**Erreur (400 Bad Request)** :
```json
{
  "error": "Le fichier doit être un fichier ZIP contenant un shapefile"
}
```

**Erreur (500 Internal Server Error)** :
```json
{
  "error": "Erreur lors de l'import: Unable to open datasource"
}
```

**Exemple cURL** :
```bash
curl -X POST http://localhost:8000/api/upload-shapefile/ \
  -F "file=@captages.zip" \
  -F "name=Captages AEP" \
  -F "description=Points de captage" \
  -F "identifier_field=code_bss" \
  -F "style_color=#00ff00"
```

**Exemple JavaScript (FormData)** :
```javascript
const uploadShapefile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', 'Captages AEP');
  formData.append('identifier_field', 'code_bss');
  formData.append('style_color', '#00ff00');

  const response = await axios.post(
    'http://localhost:8000/api/upload-shapefile/',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' }
    }
  );

  console.log('Couche créée :', response.data);
};
```

---

### Export

#### **GET** `/api/export/commune/{code_insee}/`

Générer et télécharger une **fiche de synthèse PDF** pour une commune.

**Paramètres** :
- `code_insee` (string, path) : Code INSEE de la commune (ex: "07186")

**Réponse (200 OK)** :
- **Content-Type** : `application/pdf`
- **Content-Disposition** : `attachment; filename="fiche_commune_{code_insee}.pdf"`

**Erreur (404 Not Found)** :
```json
{
  "error": "Commune non trouvée"
}
```

**Exemple cURL (téléchargement)** :
```bash
curl http://localhost:8000/api/export/commune/07186/ \
  -o fiche_privas.pdf
```

**Exemple JavaScript (téléchargement)** :
```javascript
const downloadPDF = async (codeInsee) => {
  const response = await axios.get(
    `http://localhost:8000/api/export/commune/${codeInsee}/`,
    { responseType: 'blob' }
  );

  // Créer un lien de téléchargement
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `fiche_commune_${codeInsee}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

downloadPDF('07186');
```

---

#### **GET** `/api/preview/commune/{code_insee}/`

Prévisualiser la fiche de synthèse au format **HTML** (avant génération PDF).

**Paramètres** :
- `code_insee` (string, path) : Code INSEE de la commune

**Réponse (200 OK)** :
- **Content-Type** : `text/html`

**Exemple cURL** :
```bash
curl http://localhost:8000/api/preview/commune/07186/
```

**Exemple (ouvrir dans le navigateur)** :
```
http://localhost:8000/api/preview/commune/07186/
```

---

## Codes d'erreur

| Code | Signification              | Exemple                                      |
|------|----------------------------|----------------------------------------------|
| 200  | OK                         | Requête réussie                              |
| 201  | Created                    | Ressource créée avec succès                  |
| 204  | No Content                 | Suppression réussie                          |
| 400  | Bad Request                | Données invalides, fichier incorrect         |
| 404  | Not Found                  | Couche ou commune introuvable                |
| 500  | Internal Server Error      | Erreur serveur (import échoué, BDD, etc.)    |

---

## Exemples d'utilisation

### Scénario complet : Import et affichage d'une couche

**Étape 1 : Importer un ShapeFile**
```bash
curl -X POST http://localhost:8000/api/upload-shapefile/ \
  -F "file=@communes.zip" \
  -F "name=Communes Ardèche" \
  -F "identifier_field=code_insee"
```

**Réponse :**
```json
{
  "id": 1,
  "name": "Communes Ardèche",
  "feature_count": 335
}
```

**Étape 2 : Récupérer le GeoJSON**
```bash
curl http://localhost:8000/api/layers/1/geojson/ > communes.geojson
```

**Étape 3 : Afficher sur une carte Leaflet**
```javascript
import L from 'leaflet';
import axios from 'axios';

const map = L.map('map').setView([44.73, 4.60], 10);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

const loadLayer = async () => {
  const { data } = await axios.get('http://localhost:8000/api/layers/1/geojson/');
  L.geoJSON(data, {
    style: {
      color: '#3388ff',
      weight: 2,
      fillOpacity: 0.2
    },
    onEachFeature: (feature, layer) => {
      layer.bindPopup(`<strong>${feature.properties.nom}</strong>`);
    }
  }).addTo(map);
};

loadLayer();
```

---

### Scénario : Calculer des statistiques sur une couche

```javascript
// Récupérer uniquement les propriétés (optimisé)
const { data } = await axios.get('http://localhost:8000/api/layers/2/properties/');

// Calculer la population totale
const totalPopulation = data.features.reduce(
  (sum, f) => sum + (f.properties.population || 0),
  0
);

console.log(`Population totale : ${totalPopulation.toLocaleString()} habitants`);

// Trouver les communes avec population > 5000
const grandesCommunes = data.features.filter(
  f => (f.properties.population || 0) > 5000
);

console.log(`${grandesCommunes.length} communes de plus de 5000 habitants`);
```

---

### Scénario : Générer un PDF par lot

```bash
# Générer les fiches PDF pour plusieurs communes
for code in 07186 07019 07102; do
  curl "http://localhost:8000/api/export/commune/${code}/" \
    -o "fiche_${code}.pdf"
  echo "Fiche ${code} générée"
done
```

---

## Pagination (future)

Pour les couches avec un très grand nombre de features, la pagination sera ajoutée :

```bash
GET /api/layers/1/geojson/?page=1&page_size=1000
```

---

## Filtrage (future)

Filtrer les features par propriété :

```bash
GET /api/layers/1/geojson/?filter=population__gt=5000
GET /api/layers/2/geojson/?filter=qualite=Bonne
```

---

## Ressources

- [Django REST Framework](https://www.django-rest-framework.org/)
- [GeoJSON Specification](https://geojson.org/)
- [PostGIS Documentation](https://postgis.net/docs/)
- [Leaflet.js](https://leafletjs.com/)

---

## Support

Pour signaler un bug ou demander une fonctionnalité, ouvrir une issue sur le dépôt Git du projet.
