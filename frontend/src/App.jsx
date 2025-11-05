import { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, useMap, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';
import { API_BASE_URL } from './config';
import Navbar from './components/Navbar';
import './components/Navbar.css';
import Sidebar from './components/Sidebar';
import './components/Sidebar.css';
import Dashboard from './components/Dashboard';
import './components/Dashboard.css';
import Export from './components/Export';
import './components/Export.css';
import LayerManager from './components/LayerManager';
import './components/LayerManager.css';
import AttributePanel from './components/AttributePanel';
import './components/AttributePanel.css';
import MapToolbar from './components/MapToolbar';
import './components/MapToolbar.css';
import MapTools from './components/MapTools';
import GeoJSONLayer from './components/GeoJSONLayer';
import { useLayerContext } from './contexts/LayerContext';
import MapScale from './components/MapScale';
import MouseCoordinates from './components/MouseCoordinates';
import UserManagement from './components/UserManagement';
import './components/UserManagement.css';
import UserProfile from './components/UserProfile';
import './components/UserProfile.css';
import ForcePasswordChange from './components/ForcePasswordChange';
import PasswordChangePrompt from './components/PasswordChangePrompt';
import { useAuth } from './contexts/AuthContext';

/**
 * Composant utilitaire pour recalculer la taille de la carte
 * lors de l'affichage/masquage de la sidebar
 */
function MapResizer({ sidebarVisible }) {
  const map = useMap();

  useEffect(() => {
    // Petit délai pour laisser la transition CSS se terminer
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 350);

    return () => clearTimeout(timer);
  }, [sidebarVisible, map]);

  return null;
}

/**
 * Composant pour initialiser les panes personnalisés pour la gestion de l'ordre des couches
 * Crée des panes avec des z-index différents pour contrôler l'empilement des couches vectorielles
 * Met à jour les z-index quand l'ordre des couches change
 */
function LayerPanesInitializer({ layers }) {
  const map = useMap();

  useEffect(() => {
    // Créer un pane pour chaque valeur d'order unique
    const orderValues = new Set(layers.map(l => l.order || 0));

    orderValues.forEach(order => {
      const paneName = `layer-order-${order}`;

      // Créer le pane s'il n'existe pas
      if (!map.getPane(paneName)) {
        const pane = map.createPane(paneName);
        // Z-index de base pour overlays = 400
        // On ajoute l'order pour avoir le bon empilement
        pane.style.zIndex = 400 + order;
        pane.style.pointerEvents = 'auto';
      } else {
        // Mettre à jour le z-index si le pane existe déjà
        const pane = map.getPane(paneName);
        if (pane) {
          pane.style.zIndex = 400 + order;
        }
      }
    });
  }, [map, layers]);

  return null;
}

function App() {
  const [currentPage, setCurrentPage] = useState('map');
  const [baseLayer, setBaseLayer] = useState('bdortho');
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [selectedFeatures, setSelectedFeatures] = useState([]);
  const [activeTool, setActiveTool] = useState('select');
  const [showPasswordChange, setShowPasswordChange] = useState(false);

  const { layers, layersData, activeLayerId } = useLayerContext();
  const { user } = useAuth();

  // Si l'utilisateur doit changer son mot de passe
  if (user?.must_change_password) {
    // Si l'utilisateur a choisi de changer son mot de passe, afficher la page de changement
    if (showPasswordChange) {
      return (
        <>
          <Navbar currentPage="password-change" onPageChange={() => {}} />
          <ForcePasswordChange
            user={user}
            onPasswordChanged={() => {
              // Recharger la page pour récupérer l'utilisateur mis à jour
              window.location.reload();
            }}
          />
        </>
      );
    }

    // Sinon, afficher la fenêtre de choix
    return (
      <>
        <Navbar currentPage="password-prompt" onPageChange={() => {}} />
        <PasswordChangePrompt
          user={user}
          onChangePassword={() => {
            setShowPasswordChange(true);
          }}
          onKeepPassword={() => {
            // Recharger la page pour récupérer l'utilisateur mis à jour
            window.location.reload();
          }}
        />
      </>
    );
  }

  // Utiliser une ref pour avoir toujours la valeur à jour dans les callbacks
  const activeLayerIdRef = useRef(activeLayerId);

  useEffect(() => {
    activeLayerIdRef.current = activeLayerId;
  }, [activeLayerId]);

  // Réinitialiser l'état de la carte quand on quitte la page map
  useEffect(() => {
    if (currentPage !== 'map') {
      // Réinitialiser l'outil à 'select'
      setActiveTool('select');
      // Désélectionner toutes les features
      setSelectedFeature(null);
      setSelectedFeatures([]);
    }
  }, [currentPage]);

  // Réinitialiser la sélection quand on change de couche active
  useEffect(() => {
    setSelectedFeature(null);
    setSelectedFeatures([]);
  }, [activeLayerId]);

  const handleToolSelect = (toolId) => {
    setActiveTool(toolId);
  };

  const handleFeatureClick = (feature, layerId) => {
    if (activeTool === 'select' || activeTool === 'info') {
      const currentActiveLayerId = activeLayerIdRef.current;

      // Vérifier si une couche active est définie
      if (currentActiveLayerId === null || currentActiveLayerId === undefined) {
        console.warn('Aucune couche active. Veuillez sélectionner une couche dans le panneau latéral.');
        return;
      }

      // Vérifier que le clic est sur la couche active
      if (Number(layerId) !== Number(currentActiveLayerId)) {
        return;
      }

      setSelectedFeature(feature);
      setSelectedFeatures([feature]);
    }
  };

  const handleFeatureSelect = (features) => {
    setSelectedFeatures(features);
    if (features.length > 0) {
      setSelectedFeature(features[0]);
    }
  };

  const handleMeasureComplete = (measurement) => {
    console.log('Mesure complétée:', measurement);
  };

  const handleBaseLayerChange = (layer) => {
    setBaseLayer(layer);
  };

  const baseLayers = {
    osm: {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 19
    },
    bdortho: {
      url: "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=HR.ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg",
      attribution: "&copy; IGN - BD ORTHO",
      maxZoom: 19
    },
    scan25: {
      url: "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg",
      attribution: "&copy; IGN - SCAN 25",
      maxZoom: 16
    },
    satellite: {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      attribution: "&copy; Esri",
      maxZoom: 19
    }
  };

  return (
    <div style ={{ height: '100vh', width: '100vw', position: 'relative', overflow: 'hidden' }}>
      <Navbar currentPage={currentPage} onPageChange={setCurrentPage} />

      {/* Contenu de la carte - toujours présent mais caché si pas sur la page map */}
      <div style={{ display: currentPage === 'map' ? 'block' : 'none' }}>
        {/* Barre d'outils SIG */}
        <MapToolbar
          onToolSelect={handleToolSelect}
          activeTool={activeTool}
        />

        {sidebarVisible && (
          <Sidebar
            baseLayer={baseLayer}
            onBaseLayerChange={handleBaseLayerChange}
          />
        )}

        {/* Bouton toggle sidebar */}
        <button
          onClick={() => setSidebarVisible(!sidebarVisible)}
          style={{
            position: 'fixed',
            top: 70,
            left: sidebarVisible ? 330 : 10,
            zIndex: 1001,
            padding: '8px 12px',
            fontSize: '14px',
            cursor: 'pointer',
            background: 'white',
            border: '2px solid #ccc',
            borderRadius: '4px',
            transition: 'left 0.3s'
          }}
        >
          {sidebarVisible ? '◀ Masquer' : '▶ Afficher'}
        </button>

        <div style={{
          position: 'absolute',
          top: 60,
          left: sidebarVisible ? '320px' : '0',
          right: 0,
          bottom: 0,
          transition: 'left 0.3s'
        }}>
        <MapContainer
          center={[45.75, 4.85]}
          zoom={10}
          zoomControl={false}
          minZoom={2}
          style={{ height: '100%', width: '100%' }}
        >
          <MapResizer sidebarVisible={sidebarVisible} />
          <LayerPanesInitializer layers={layers} />
          <ZoomControl position="topleft" />

          {baseLayer === 'bdortho' ? (
            <>
              {/* Couche de fond OpenStreetMap */}
              <TileLayer
                key="osm-base"
                url={baseLayers.osm.url}
                attribution={baseLayers.osm.attribution}
                maxZoom={baseLayers.osm.maxZoom}
              />
              {/* BD ORTHO par-dessus */}
              <TileLayer
                key="bdortho"
                url={baseLayers.bdortho.url}
                attribution={baseLayers.bdortho.attribution}
                maxZoom={baseLayers.bdortho.maxZoom}
              />
            </>
          ) : (
            /* Autres couches */
            <TileLayer
              key={baseLayer}
              url={baseLayers[baseLayer].url}
              attribution={baseLayers[baseLayer].attribution}
              maxZoom={baseLayers[baseLayer].maxZoom}
            />
          )}

          {/* Couches importées - triées par order croissant pour que les couches avec order élevé soient créées en dernier (donc au-dessus) */}
          {[...layers]
            .sort((a, b) => (a.order || 0) - (b.order || 0))
            .map((layer) => {
              if (!layer.visible || !layersData[layer.id]) return null;

              return (
                <GeoJSONLayer
                  key={`layer-${layer.id}-order-${layer.order}`}
                  data={layersData[layer.id]}
                  selectedFeatures={selectedFeatures}
                  onFeatureClick={handleFeatureClick}
                  identifierField={layer.identifier_field}
                  baseStyle={{
                    color: layer.style_color,
                    // ... other style properties
                    weight: layer.style_weight,
                    opacity: layer.style_opacity,
                    fillOpacity: layer.style_fill_opacity
                  }}
                  visible={layer.visible}
                  order={layer.order}
                  layerId={layer.id}
                  isActive={activeLayerId === layer.id}
                />
              );
            })}

          {/* Outils SIG (mesure, sélection, etc.) */}
          <MapTools
            activeTool={activeTool}
            onFeatureSelect={handleFeatureSelect}
            onMeasureComplete={handleMeasureComplete}
            activeLayerId={activeLayerId}
            layers={layers}
            layersData={layersData}
          />

          {/* Échelle de la carte */}
          <MapScale />

          {/* Coordonnées de la souris */}
          <MouseCoordinates />
          </MapContainer>
        </div>

        {/* Panneau d'attributs */}
        {selectedFeature && (
          <AttributePanel
            feature={selectedFeature}
            features={selectedFeatures}
            onClose={() => {
              setSelectedFeature(null);
              setSelectedFeatures([]);
            }}
            onExportPDF={(codeInsee) => {
              window.open(`${API_BASE_URL}/api/export/commune/${codeInsee}/`, '_blank');
            }}
          />
        )}
      </div>

      {currentPage === 'dashboard' && (
        <div style={{
          position: 'absolute',
          top: 60,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: 'auto'
        }}>
          <Dashboard />
        </div>
      )}

      {currentPage === 'layers' && (
        <div style={{
          position: 'absolute',
          top: 60,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: 'auto',
          background: '#f3f4f6'
        }}>
          <LayerManager />
        </div>
      )}

      {currentPage === 'export' && (
        <div style={{
          position: 'absolute',
          top: 60,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: 'auto'
        }}>
          <Export />
        </div>
      )}

      {currentPage === 'users' && (
        <div style={{
          position: 'absolute',
          top: 60,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: 'auto'
        }}>
          <UserManagement />
        </div>
      )}

      {currentPage === 'profile' && (
        <div style={{
          position: 'absolute',
          top: 60,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: 'auto'
        }}>
          <UserProfile />
        </div>
      )}
    </div>
  );
}

export default App;
