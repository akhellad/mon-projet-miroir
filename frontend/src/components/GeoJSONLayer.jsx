import { GeoJSON } from 'react-leaflet';
import { useMemo, useEffect, useRef } from 'react';
import L from 'leaflet';

/**
 * Composant générique pour afficher des couches GeoJSON sur la carte
 * - Supporte tous types de géométries (Point, LineString, Polygon, etc.)
 * - Gère la sélection visuelle des entités
 * - Optimise le rendu avec Canvas pour les grandes couches (>1000 entités)
 *
 * @param {Object} data - Données GeoJSON à afficher
 * @param {Array} selectedFeatures - Liste des entités sélectionnées
 * @param {Function} onFeatureClick - Callback au clic sur une entité
 * @param {Object} baseStyle - Style par défaut des entités
 * @param {Object} selectedStyle - Style des entités sélectionnées
 * @param {String} identifierField - Champ identifiant (ex: 'code_insee', 'id')
 * @param {Boolean} visible - Visibilité de la couche
 */
function GeoJSONLayer({
  data,
  selectedFeatures = [],
  onFeatureClick,
  baseStyle = {},
  selectedStyle = {},
  identifierField = null,
  visible = true
}) {
  // Styles par défaut
  const defaultBaseStyle = {
    color: '#3388ff',
    weight: 2,
    opacity: 0.8,
    fillOpacity: 0.2
  };

  const defaultSelectedStyle = {
    color: '#ef4444',
    weight: 3,
    opacity: 1,
    fillOpacity: 0.3
  };

  // Fusion des styles personnalisés avec les styles par défaut
  const finalBaseStyle = { ...defaultBaseStyle, ...baseStyle };
  const finalSelectedStyle = { ...defaultSelectedStyle, ...selectedStyle };

  /**
   * Extrait l'identifiant unique d'une entité
   * Priorité : identifierField > id > code_insee > autres champs
   */
  const getFeatureId = (feature) => {
    if (!feature) return null;

    if (identifierField) {
      if (feature.properties?.[identifierField] !== undefined) {
        return String(feature.properties[identifierField]);
      }
      if (feature[identifierField] !== undefined) {
        return String(feature[identifierField]);
      }
    }

    // Recherche dans les champs standards
    return String(feature.id ||
           feature.properties?.code_insee ||
           feature.properties?.id ||
           feature.properties?.name ||
           feature.properties?.nom ||
           JSON.stringify(feature.geometry?.coordinates?.[0] || feature.properties));
  };

  /**
   * Retourne le style approprié selon l'état de sélection
   */
  const getStyle = (feature) => {
    const featureId = getFeatureId(feature);
    const isSelected = selectedFeatures.some(f => getFeatureId(f) === featureId);

    return isSelected ? finalSelectedStyle : finalBaseStyle;
  };

  // Référence pour stocker toutes les couches Leaflet
  const layersRef = useRef({});

  /**
   * Configure les événements et le style pour chaque entité
   */
  const onEachFeature = (feature, layer) => {
    const featureId = getFeatureId(feature);
    layersRef.current[featureId] = layer;

    if (onFeatureClick) {
      layer.on({
        click: () => {
          if (layer.bringToFront) {
            layer.bringToFront();
          }
          onFeatureClick(feature);
        }
      });
    }

    // Mettre au premier plan si l'entité est sélectionnée
    const isSelected = selectedFeatures.some(f => getFeatureId(f) === featureId);
    if (isSelected && layer.bringToFront) {
      layer.bringToFront();
    }
  };

  /**
   * Met à jour le style et l'ordre d'affichage lorsque la sélection change
   */
  useEffect(() => {
    if (!data) return;

    const selectedIds = new Set(selectedFeatures.map(f => getFeatureId(f)));

    Object.keys(layersRef.current).forEach(featureId => {
      const layer = layersRef.current[featureId];
      if (!layer) return;

      const isSelected = selectedIds.has(featureId);

      if (layer.setStyle) {
        layer.setStyle(isSelected ? finalSelectedStyle : finalBaseStyle);
      }

      if (isSelected && layer.bringToFront) {
        setTimeout(() => layer.bringToFront(), 0);
      }
    });
  }, [selectedFeatures, finalSelectedStyle, finalBaseStyle, data, getFeatureId]);

  /**
   * Génère une clé unique pour forcer le re-render si les données changent
   */
  const layerKey = useMemo(() => {
    if (!data) return 'empty';
    return `${JSON.stringify(data).substring(0, 100)}`;
  }, [data]);

  /**
   * Sélectionne le moteur de rendu optimal selon le nombre d'entités
   * Canvas pour >1000 entités, SVG pour les petites couches
   */
  const renderer = useMemo(() => {
    if (data?.features && data.features.length > 1000) {
      return L.canvas({ padding: 0.5 });
    }
    return undefined;
  }, [data]);

  // Garde : ne rien afficher si la couche est invisible ou sans données
  if (!visible || !data) return null;

  return (
    <GeoJSON
      key={layerKey}
      data={data}
      style={getStyle}
      onEachFeature={onEachFeature}
      renderer={renderer}
    />
  );
}

export default GeoJSONLayer;
