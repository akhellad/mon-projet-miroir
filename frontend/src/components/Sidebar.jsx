import { useState } from 'react';
import { useLayerContext } from '../contexts/LayerContext';
import LayerPropertiesModal from './LayerPropertiesModal';

/**
 * Panneau latéral de gestion des couches
 * - Sélection du fond de carte (OSM, IGN BD ORTHO, SCAN 25, Satellite)
 * - Gestion de la visibilité et du style des couches
 * - Affichage des propriétés des couches
 */
function Sidebar({ baseLayer, onBaseLayerChange }) {
  const { layers, updateLayerVisibility, updateLayerStyle, loadLayers } = useLayerContext();
  const [selectedLayer, setSelectedLayer] = useState(null);
  const [expandedLayers, setExpandedLayers] = useState(new Set());

  const toggleLayerExpanded = (layerId) => {
    const newExpanded = new Set(expandedLayers);
    if (newExpanded.has(layerId)) {
      newExpanded.delete(layerId);
    } else {
      newExpanded.add(layerId);
    }
    setExpandedLayers(newExpanded);
  };

  const layerOptions = [
    { value: 'osm', label: 'OpenStreetMap' },
    { value: 'bdortho', label: 'IGN - BD ORTHO (Photos aériennes)' },
    { value: 'scan25', label: 'IGN - SCAN 25' },
    { value: 'satellite', label: 'Satellite (Esri)' }
  ];

  const toggleLayerVisibility = async (layer) => {
    try {
      await updateLayerVisibility(layer.id, !layer.visible);
    } catch (err) {
      console.error('Erreur toggle visibilité:', err);
    }
  };

  const handleStyleUpdate = async (layerId, styleUpdates) => {
    try {
      await updateLayerStyle(layerId, styleUpdates);
    } catch (err) {
      console.error('Erreur mise à jour style:', err);
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Gestionnaire de couches</h2>
      </div>

      {/* Fond de carte */}
      <div className="control-section">
        <h3>Fond de carte</h3>
        <select
          value={baseLayer}
          onChange={(e) => onBaseLayerChange && onBaseLayerChange(e.target.value)}
          className="layer-select"
        >
          {layerOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Liste des couches */}
      <div className="control-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ margin: 0 }}>Couches disponibles ({layers.length})</h3>
          <button
            onClick={() => loadLayers(true)}
            className="btn-refresh"
            title="Actualiser les couches"
          >
            ⟳
          </button>
        </div>

        {layers.length === 0 ? (
          <p className="no-layers-text">Aucune couche importée</p>
        ) : (
          <div className="layers-list-sidebar">
            {layers.map(layer => {
              const isExpanded = expandedLayers.has(layer.id);
              return (
                <div key={layer.id} className="layer-item-accordion">
                  <div className="layer-item-header" onClick={() => toggleLayerExpanded(layer.id)}>
                    <div className="layer-header-left">
                      <span className="layer-expand-icon">
                        {isExpanded ? '▼' : '▶'}
                      </span>
                      <input
                        type="checkbox"
                        checked={layer.visible}
                        onChange={(e) => {
                          e.stopPropagation();
                          toggleLayerVisibility(layer);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        className="layer-checkbox-input"
                      />
                      <div
                        className="layer-color-dot"
                        style={{ backgroundColor: layer.style_color }}
                      />
                      <span className="layer-name">{layer.name}</span>
                    </div>
                    <span className="layer-feature-count">{layer.feature_count} entités</span>
                  </div>

                  {isExpanded && (
                    <div className="layer-item-details">
                      <div className="layer-detail-row">
                        <span className="layer-detail-label">Type de géométrie:</span>
                        <span className="layer-detail-value">{layer.geometry_type}</span>
                      </div>
                      <div className="layer-detail-row">
                        <span className="layer-detail-label">Système de coordonnées:</span>
                        <span className="layer-detail-value">EPSG:{layer.srid}</span>
                      </div>
                      <div className="layer-detail-row">
                        <span className="layer-detail-label">Nombre d'entités:</span>
                        <span className="layer-detail-value">{layer.feature_count.toLocaleString('fr-FR')}</span>
                      </div>
                      <div className="layer-detail-row">
                        <span className="layer-detail-label">Champ identifiant:</span>
                        <span className="layer-detail-value"><code>{layer.identifier_field}</code></span>
                      </div>
                      {layer.description && (
                        <div className="layer-detail-row">
                          <span className="layer-detail-label">Description:</span>
                          <span className="layer-detail-value">{layer.description}</span>
                        </div>
                      )}
                      <button
                        className="layer-properties-btn-expanded"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLayer(layer);
                        }}
                      >
                        ⚙️ Modifier les propriétés
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal des propriétés */}
      {selectedLayer && (
        <LayerPropertiesModal
          layer={selectedLayer}
          onClose={() => setSelectedLayer(null)}
          onUpdate={handleStyleUpdate}
        />
      )}
    </div>
  );
}

export default Sidebar;
