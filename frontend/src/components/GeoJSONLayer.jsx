import { GeoJSON } from 'react-leaflet';
import { useEffect, useRef, useCallback } from 'react';
import L from 'leaflet';

/**
 * Composant générique pour afficher des couches GeoJSON sur la carte
 * - Supporte tous types de géométries (Point, LineString, Polygon, etc.)
 * - Gère la sélection visuelle des entités
 * - Optimise le rendu avec Canvas pour les grandes couches (>1000 entités)
 * - L'ordre d'affichage est géré par l'ordre de création des composants
 *
 * @param {Object} data - Données GeoJSON à afficher
 * @param {Array} selectedFeatures - Liste des entités sélectionnées
 * @param {Function} onFeatureClick - Callback au clic sur une entité
 * @param {Object} baseStyle - Style par défaut des entités
 * @param {Object} selectedStyle - Style des entités sélectionnées
 * @param {String} identifierField - Champ identifiant (ex: 'code_insee', 'id')
 * @param {Boolean} visible - Visibilité de la couche.
 * @param {Number} order - Ordre de la couche pour le z-index.
 * @param {Number} layerId - ID de la couche pour vérifier si elle est active
 * @param {Boolean} isActive - Indique si cette couche est la couche active pour interaction
 */
function GeoJSONLayer({
  data,
  selectedFeatures = [],
  onFeatureClick,
  baseStyle = {},
  selectedStyle = {},
  identifierField = null,
  visible = true,
  order = 0, // Default order to 0 if not provided
  layerId = null,
  isActive = false
}) {
  const geoJsonRef = useRef(); // Ref to the GeoJSON component instance

  // Nom du pane basé sur l'ordre (les panes sont créés au niveau de la carte dans App.jsx)
  const paneName = `layer-order-${order}`;

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
  const getFeatureId = useCallback((feature) => {
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
  }, [identifierField]);

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
   * Convertit les points en cercles au lieu de marqueurs
   * Note: Les CircleMarker n'utilisent pas le pane comme les polygones,
   * mais on peut définir leur pane aussi pour la cohérence
   */
  const pointToLayer = (feature, latlng) => {
    const style = getStyle(feature);
    return L.circleMarker(latlng, {
      radius: 5,  // Rayon du cercle en pixels
      ...style,
      pane: paneName  // Utiliser le même pane que les autres géométries
    });
  };

  /**
   * Configure les événements et le style pour chaque entité
   * Passe le layerId au callback pour vérification dans App.jsx
   */
  const onEachFeature = useCallback((feature, layer) => {
    const featureId = getFeatureId(feature);
    layersRef.current[featureId] = layer;

    if (onFeatureClick) {
      layer.on({
        click: () => {
          // Toujours déclencher le callback avec le layerId pour que App.jsx puisse vérifier
          onFeatureClick(feature, layerId);
        }
      });
    }

    // Modifier le curseur en fonction de l'état actif
    layer.on({
      mouseover: () => {
        if (isActive) {
          layer.getElement()?.style && (layer.getElement().style.cursor = 'pointer');
        }
      },
      mouseout: () => {
        if (isActive) {
          layer.getElement()?.style && (layer.getElement().style.cursor = '');
        }
      }
    });
  }, [onFeatureClick, getFeatureId, isActive, layerId]);


  /**
   * Met à jour le style lorsque la sélection change
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
    });
  }, [selectedFeatures, finalSelectedStyle, finalBaseStyle, data]);


  /**
   * Désactivation du renderer Canvas car il cause des conflits avec les panes personnalisés
   * Le renderer SVG par défaut fonctionne bien pour la plupart des cas d'usage
   */
  const renderer = undefined;

  // Garde : ne rien afficher si la couche est invisible ou sans données
  if (!visible || !data) return null;

  return (
    <GeoJSON
      ref={geoJsonRef}
      data={data}
      style={getStyle}
      onEachFeature={onEachFeature}
      pointToLayer={pointToLayer}
      renderer={renderer}
      pane={paneName}
    />
  );
}

export default GeoJSONLayer;
