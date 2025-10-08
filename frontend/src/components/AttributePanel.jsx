import { useState, useMemo } from 'react';
import './AttributePanel.css';
import * as turf from '@turf/turf';

/**
 * Panneau d'affichage des attributs et informations géométriques des entités sélectionnées
 * Supporte l'affichage d'une ou plusieurs entités avec calculs automatiques (surface, périmètre, longueur)
 *
 * @param {Object} feature - Entité unique à afficher (format GeoJSON)
 * @param {Array} features - Tableau d'entités pour sélection multiple
 * @param {Function} onClose - Callback de fermeture du panneau
 * @param {Function} onExportPDF - Callback d'export PDF (optionnel)
 */
function AttributePanel({ feature, features, onClose, onExportPDF }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [selectedFeatureIndex, setSelectedFeatureIndex] = useState(0);
  const [expandedFeatures, setExpandedFeatures] = useState(new Set([0]));

  // Détection du mode sélection multiple
  const isMultiSelection = features && features.length > 1;
  const currentFeature = isMultiSelection ? features[selectedFeatureIndex] : (feature || features[0]);
  const properties = currentFeature?.properties || {};

  /**
   * Génère un label lisible pour une entité
   * Recherche dans l'ordre : nom, name, code_insee, id ou valeur par défaut
   */
  const getFeatureLabel = (feat, index) => {
    if (!feat || !feat.properties) return `Entité ${index + 1}`;

    const props = feat.properties;
    return props.nom || props.name || props.code_insee || props.id || `Entité ${index + 1}`;
  };

  /**
   * Gère le dépliage/repliage d'une entité dans la liste
   */
  const toggleFeature = (index) => {
    const newExpanded = new Set(expandedFeatures);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedFeatures(newExpanded);
    setSelectedFeatureIndex(index);
  };

  /**
   * Calcule les informations géométriques de l'entité courante
   * - Points : coordonnées (lat, lon)
   * - Lignes : longueur (m ou km)
   * - Polygones : surface (m², ha, km²) et périmètre (m ou km)
   * Utilise Turf.js pour les calculs géographiques
   */
  const geometryInfo = useMemo(() => {
    if (!currentFeature || !currentFeature.geometry) return null;

    const geom = currentFeature.geometry;
    const info = {
      type: geom.type,
      typeLabel: getGeometryTypeLabel(geom.type)
    };

    try {
      if (geom.type === 'Point' || geom.type === 'MultiPoint') {
        // Extraction et formatage des coordonnées
        const coords = geom.type === 'Point' ? geom.coordinates : geom.coordinates[0];
        info.coordinates = `${coords[1].toFixed(6)}, ${coords[0].toFixed(6)}`;
      } else if (geom.type === 'LineString' || geom.type === 'MultiLineString') {
        // Calcul de la longueur avec formatage adapté
        const line = turf.lineString(geom.coordinates);
        const length = turf.length(line, { units: 'kilometers' });
        info.length = length >= 1 ? `${length.toFixed(2)} km` : `${(length * 1000).toFixed(0)} m`;
      } else if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') {
        // Calcul de la surface avec formatage adapté (m², ha, km²)
        const polygon = geom.type === 'Polygon'
          ? turf.polygon(geom.coordinates)
          : turf.multiPolygon(geom.coordinates);
        const area = turf.area(polygon);
        info.area = area >= 10000
          ? `${(area / 10000).toFixed(2)} ha`
          : area >= 1000000
          ? `${(area / 1000000).toFixed(2)} km²`
          : `${area.toFixed(0)} m²`;

        // Calcul du périmètre
        const boundary = turf.polygonToLine(polygon);
        const perimeter = turf.length(boundary, { units: 'kilometers' });
        info.perimeter = perimeter >= 1 ? `${perimeter.toFixed(2)} km` : `${(perimeter * 1000).toFixed(0)} m`;
      }
    } catch (error) {
      console.error('Erreur calcul géométrie:', error);
    }

    return info;
  }, [currentFeature]);

  /**
   * Convertit le type de géométrie en label français
   */
  function getGeometryTypeLabel(type) {
    const labels = {
      'Point': 'Point',
      'MultiPoint': 'Multi-points',
      'LineString': 'Ligne',
      'MultiLineString': 'Multi-lignes',
      'Polygon': 'Polygone',
      'MultiPolygon': 'Multi-polygones'
    };
    return labels[type] || type;
  }

  /**
   * Formate les noms de champs : snake_case -> Title Case
   * Exemple : code_insee -> Code Insee
   */
  function formatFieldName(key) {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  /**
   * Formate les valeurs des champs selon leur type
   * Gère les nombres avec séparateurs de milliers (format français)
   */
  function formatFieldValue(value) {
    if (value === null || value === undefined) return 'N/A';

    if (typeof value === 'number') {
      return value.toLocaleString('fr-FR');
    }

    return String(value);
  }

  /**
   * Calcule les informations géométriques simplifiées pour la liste en mode multi-sélection
   * Retourne uniquement la surface pour les polygones
   */
  function getFeatureGeomInfo(feat) {
    if (!feat || !feat.geometry) return null;
    const geom = feat.geometry;
    const info = { type: geom.type, typeLabel: getGeometryTypeLabel(geom.type) };

    try {
      if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') {
        const polygon = geom.type === 'Polygon'
          ? turf.polygon(geom.coordinates)
          : turf.multiPolygon(geom.coordinates);
        const area = turf.area(polygon);
        info.area = area >= 10000
          ? `${(area / 10000).toFixed(2)} ha`
          : `${area.toFixed(0)} m²`;
      }
    } catch (error) {
      console.error('Erreur calcul géométrie:', error);
    }
    return info;
  }

  // Garde : ne rien afficher si aucune entité n'est fournie
  if (!feature && (!features || features.length === 0)) return null;

  return (
    <div className={`attribute-panel ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="attribute-panel-header">
        <h3>Informations attributaires</h3>
        <div className="header-actions">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="collapse-btn"
            title={isCollapsed ? "Développer" : "Réduire"}
          >
            {isCollapsed ? '◀' : '▶'}
          </button>
          <button onClick={onClose} className="close-btn" title="Fermer">
            ✕
          </button>
        </div>
      </div>

      <div className="attribute-panel-content">
        {/* Mode sélection multiple : affichage en liste accordéon */}
        {isMultiSelection ? (
          <div className="multi-selection-container">

            <div className="features-list">
              {features.map((feat, index) => {
                const isExpanded = expandedFeatures.has(index);
                const featProps = feat?.properties || {};
                const featGeomInfo = getFeatureGeomInfo(feat);

                return (
                  <div key={index} className="feature-item">
                    <div
                      className="feature-item-header"
                      onClick={() => toggleFeature(index)}
                    >
                      <div className="feature-item-title">
                        <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                        <span className="feature-label">{getFeatureLabel(feat, index)}</span>
                      </div>
                      {featGeomInfo && (
                        <span className="feature-type-badge">{featGeomInfo.typeLabel}</span>
                      )}
                    </div>

                    {isExpanded && (
                      <div className="feature-item-content">
                        {/* Affichage des attributs de l'entité */}
                        {Object.keys(featProps).length > 0 && (
                          <div className="feature-attributes">
                            {Object.entries(featProps).map(([key, value]) => (
                              <div key={key} className="attribute-row-compact">
                                <span className="attribute-label-compact">{formatFieldName(key)}:</span>
                                <span className="attribute-value-compact">
                                  {formatFieldValue(value)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Affichage de la surface (polygones uniquement) */}
                        {featGeomInfo && featGeomInfo.area && (
                          <div className="feature-geometry">
                            <div className="attribute-row-compact">
                              <span className="attribute-label-compact">Surface:</span>
                              <span className="attribute-value-compact highlight">{featGeomInfo.area}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <>
            {/* Mode entité unique : affichage détaillé des attributs */}
            {Object.keys(properties).length > 0 && (
              <div className="attribute-section">
                <div className="attribute-section-title">ATTRIBUTS</div>
                {Object.entries(properties).map(([key, value]) => (
                  <div key={key} className="attribute-row">
                    <span className="attribute-label">{formatFieldName(key)}</span>
                    <span className={`attribute-value ${key === 'population' ? 'highlight' : ''}`}>
                      {formatFieldValue(value)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Section géométrie : affichage des mesures calculées (mode simple uniquement) */}
        {!isMultiSelection && geometryInfo && (
          <div className="attribute-section">
            <div className="attribute-section-title">GÉOMÉTRIE</div>
            <div className="attribute-row">
              <span className="attribute-label">Type</span>
              <span className="attribute-value">{geometryInfo.typeLabel}</span>
            </div>

            {geometryInfo.coordinates && (
              <div className="attribute-row">
                <span className="attribute-label">Coordonnées</span>
                <span className="attribute-value">{geometryInfo.coordinates}</span>
              </div>
            )}

            {geometryInfo.length && (
              <div className="attribute-row">
                <span className="attribute-label">Longueur</span>
                <span className="attribute-value highlight">{geometryInfo.length}</span>
              </div>
            )}

            {geometryInfo.area && (
              <div className="attribute-row">
                <span className="attribute-label">Surface</span>
                <span className="attribute-value highlight">{geometryInfo.area}</span>
              </div>
            )}

            {geometryInfo.perimeter && (
              <div className="attribute-row">
                <span className="attribute-label">Périmètre</span>
                <span className="attribute-value">{geometryInfo.perimeter}</span>
              </div>
            )}
          </div>
        )}

        {/* Bouton d'export PDF (disponible si code INSEE présent) */}
        {properties.code_insee && onExportPDF && (
          <div className="attribute-actions">
            <button
              className="btn-action btn-primary"
              onClick={() => onExportPDF(properties.code_insee)}
            >
              Exporter la fiche PDF
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default AttributePanel;
