import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import * as turf from '@turf/turf';

/**
 * Gestionnaire des outils interactifs de la carte
 * - Sélection simple et par rectangle
 * - Mesures de distance et surface
 * - Navigation avec molette de souris
 */
function MapTools({ activeTool, onFeatureSelect, onMeasureComplete }) {
  const map = useMap();
  const drawControlRef = useRef(null);
  const drawnItemsRef = useRef(new L.FeatureGroup());
  const measureLayerRef = useRef(new L.FeatureGroup());
  const selectedLayersRef = useRef([]); // Pour stocker les couches sélectionnées
  const middleMousePanningRef = useRef({
    active: false,
    startPoint: null
  });

  useEffect(() => {
    // Ajouter les layers au map
    map.addLayer(drawnItemsRef.current);
    map.addLayer(measureLayerRef.current);

    return () => {
      map.removeLayer(drawnItemsRef.current);
      map.removeLayer(measureLayerRef.current);
    };
  }, [map]);

  // Gestion du déplacement avec la molette (clic du milieu)
  useEffect(() => {
    const container = map.getContainer();

    const onMiddleMouseDown = (e) => {
      // Bouton du milieu (molette)
      if (e.button === 1) {
        e.preventDefault();
        middleMousePanningRef.current.active = true;
        middleMousePanningRef.current.startPoint = { x: e.clientX, y: e.clientY };
        container.style.cursor = 'grabbing';

        // Désactiver le drag normal de Leaflet temporairement
        map.dragging.disable();
      }
    };

    const onMiddleMouseMove = (e) => {
      if (!middleMousePanningRef.current.active) return;

      e.preventDefault();

      const dx = e.clientX - middleMousePanningRef.current.startPoint.x;
      const dy = e.clientY - middleMousePanningRef.current.startPoint.y;

      // Déplacer la carte
      map.panBy([-dx, -dy], { animate: false });

      middleMousePanningRef.current.startPoint = { x: e.clientX, y: e.clientY };
    };

    const onMiddleMouseUp = (e) => {
      if (e.button === 1 || middleMousePanningRef.current.active) {
        e.preventDefault();
        middleMousePanningRef.current.active = false;
        container.style.cursor = '';

        // Réactiver le drag normal de Leaflet
        map.dragging.enable();
      }
    };

    const onContextMenu = (e) => {
      // Empêcher le menu contextuel lors du clic molette
      if (middleMousePanningRef.current.active) {
        e.preventDefault();
      }
    };

    // Ajouter les event listeners
    container.addEventListener('mousedown', onMiddleMouseDown);
    container.addEventListener('mousemove', onMiddleMouseMove);
    container.addEventListener('mouseup', onMiddleMouseUp);
    container.addEventListener('contextmenu', onContextMenu);

    // Gérer le cas où la souris sort de la carte
    container.addEventListener('mouseleave', () => {
      if (middleMousePanningRef.current.active) {
        middleMousePanningRef.current.active = false;
        container.style.cursor = '';
        map.dragging.enable();
      }
    });

    return () => {
      container.removeEventListener('mousedown', onMiddleMouseDown);
      container.removeEventListener('mousemove', onMiddleMouseMove);
      container.removeEventListener('mouseup', onMiddleMouseUp);
      container.removeEventListener('contextmenu', onContextMenu);
    };
  }, [map]);

  useEffect(() => {
    // Nettoyer les contrôles existants
    if (drawControlRef.current) {
      map.removeControl(drawControlRef.current);
      drawControlRef.current = null;
    }

    // Nettoyer les mesures précédentes
    measureLayerRef.current.clearLayers();

    // Configuration selon l'outil actif
    switch (activeTool) {
      case 'selectBox':
        // Sélection par rectangle avec drag (cliquer-glisser)
        let isDrawing = false;
        let startPoint = null;
        let rectangleLayer = null;

        const onMouseDown = (e) => {
          // Ignorer si c'est le bouton du milieu (molette) ou si on est en train de panner
          if (e.originalEvent.button === 1 || middleMousePanningRef.current.active) {
            return;
          }

          // Désactiver le drag de la carte
          map.dragging.disable();

          // Supprimer le rectangle précédent
          drawnItemsRef.current.clearLayers();

          isDrawing = true;
          startPoint = e.latlng;

          // Créer un rectangle vide (rouge avec contours pointillés)
          rectangleLayer = L.rectangle([startPoint, startPoint], {
            color: '#ef4444',
            weight: 2,
            fillOpacity: 0.1,
            dashArray: '5, 5'
          }).addTo(drawnItemsRef.current);
        };

        const onMouseMove = (e) => {
          if (!isDrawing || !rectangleLayer) return;

          // Mettre à jour le rectangle
          const bounds = L.latLngBounds(startPoint, e.latlng);
          rectangleLayer.setBounds(bounds);
        };

        const onMouseUp = (e) => {
          if (!isDrawing) {
            // Si on n'est pas en train de dessiner, s'assurer que le drag est activé
            map.dragging.enable();
            return;
          }

          isDrawing = false;

          // Réactiver le drag de la carte
          map.dragging.enable();

          if (rectangleLayer && startPoint) {
            const bounds = rectangleLayer.getBounds();

            // Vérifier que le rectangle n'est pas trop petit (clic simple)
            const swPoint = map.latLngToContainerPoint(bounds.getSouthWest());
            const nePoint = map.latLngToContainerPoint(bounds.getNorthEast());
            const width = Math.abs(nePoint.x - swPoint.x);
            const height = Math.abs(nePoint.y - swPoint.y);

            if (width > 10 && height > 10) {
              // Rectangle suffisamment grand : sélection par rectangle
              selectFeaturesInBounds(bounds);
            } else {
              // Clic simple : sélectionner l'entité sous le curseur
              selectFeatureAtPoint(e.latlng);
            }

            // Toujours supprimer le rectangle après sélection
            drawnItemsRef.current.clearLayers();
          }

          startPoint = null;
          rectangleLayer = null;
        };

        // Gestionnaire pour les événements qui quittent la carte
        const onMouseOut = () => {
          if (isDrawing) {
            // Si on sort de la carte en dessinant, annuler le dessin
            isDrawing = false;
            map.dragging.enable();
            drawnItemsRef.current.clearLayers();
            startPoint = null;
            rectangleLayer = null;
          }
        };

        // Changer le curseur
        map.getContainer().style.cursor = 'crosshair';

        map.on('mousedown', onMouseDown);
        map.on('mousemove', onMouseMove);
        map.on('mouseup', onMouseUp);
        map.on('mouseout', onMouseOut);

        return () => {
          map.getContainer().style.cursor = '';
          map.dragging.enable(); // Réactiver le drag au changement d'outil
          map.off('mousedown', onMouseDown);
          map.off('mousemove', onMouseMove);
          map.off('mouseup', onMouseUp);
          map.off('mouseout', onMouseOut);
        };

      case 'measure':
        // Outil de mesure de distance
        const measureDrawControl = new L.Control.Draw({
          position: 'topleft',
          draw: {
            polyline: {
              shapeOptions: {
                color: '#ef4444',
                weight: 3
              },
              metric: true,
              feet: false
            },
            polygon: false,
            rectangle: false,
            circle: false,
            marker: false,
            circlemarker: false
          },
          edit: {
            featureGroup: measureLayerRef.current,
            remove: true
          }
        });

        map.addControl(measureDrawControl);
        drawControlRef.current = measureDrawControl;

        const handleMeasureCreated = (e) => {
          const layer = e.layer;
          measureLayerRef.current.addLayer(layer);

          // Calculer la distance avec Turf.js
          const coords = layer.getLatLngs();
          const line = turf.lineString(coords.map(c => [c.lng, c.lat]));
          const distance = turf.length(line, { units: 'kilometers' });

          // Afficher la distance
          const distanceText = distance >= 1
            ? `${distance.toFixed(2)} km`
            : `${(distance * 1000).toFixed(0)} m`;

          layer.bindPopup(`Distance: ${distanceText}`, {
            permanent: true,
            className: 'measure-label'
          }).openPopup();

          if (onMeasureComplete) {
            onMeasureComplete({ type: 'distance', value: distance, unit: 'km' });
          }
        };

        map.on(L.Draw.Event.CREATED, handleMeasureCreated);

        return () => {
          map.off(L.Draw.Event.CREATED, handleMeasureCreated);
          if (drawControlRef.current) {
            map.removeControl(drawControlRef.current);
          }
        };

      case 'measureArea':
        // Outil de mesure de surface
        const areaDrawControl = new L.Control.Draw({
          position: 'topleft',
          draw: {
            polygon: {
              shapeOptions: {
                color: '#10b981',
                weight: 3,
                fillOpacity: 0.2
              },
              metric: true,
              feet: false
            },
            polyline: false,
            rectangle: false,
            circle: false,
            marker: false,
            circlemarker: false
          },
          edit: {
            featureGroup: measureLayerRef.current,
            remove: true
          }
        });

        map.addControl(areaDrawControl);
        drawControlRef.current = areaDrawControl;

        const handleAreaCreated = (e) => {
          const layer = e.layer;
          measureLayerRef.current.addLayer(layer);

          // Calculer la surface avec Turf.js
          const coords = layer.getLatLngs()[0].map(c => [c.lng, c.lat]);
          coords.push(coords[0]); // Fermer le polygone
          const polygon = turf.polygon([coords]);
          const area = turf.area(polygon); // en m²

          // Afficher la surface
          const areaText = area >= 10000
            ? `${(area / 10000).toFixed(2)} ha`
            : area >= 1000000
            ? `${(area / 1000000).toFixed(2)} km²`
            : `${area.toFixed(0)} m²`;

          layer.bindPopup(`Surface: ${areaText}`, {
            permanent: true,
            className: 'measure-label'
          }).openPopup();

          if (onMeasureComplete) {
            onMeasureComplete({ type: 'area', value: area, unit: 'm²' });
          }
        };

        map.on(L.Draw.Event.CREATED, handleAreaCreated);

        return () => {
          map.off(L.Draw.Event.CREATED, handleAreaCreated);
          if (drawControlRef.current) {
            map.removeControl(drawControlRef.current);
          }
        };

      default:
        // Pas d'outil actif, nettoyer
        return () => {};
    }
  }, [activeTool, map]);

  // Fonction pour sélectionner une entité au clic (quand le rectangle est trop petit)
  const selectFeatureAtPoint = (latlng) => {
    // Réinitialiser la sélection précédente
    selectedLayersRef.current.forEach(layer => {
      if (layer.setStyle) {
        layer.setStyle({
          color: '#3388ff',
          weight: 2,
          opacity: 0.8,
          fillOpacity: 0.2
        });
      }
    });
    selectedLayersRef.current = [];

    // Trouver les layers à ce point
    const point = map.latLngToContainerPoint(latlng);
    const size = L.point(5, 5); // Tolérance de 5 pixels
    const bounds = L.latLngBounds(
      map.containerPointToLatLng(point.subtract(size)),
      map.containerPointToLatLng(point.add(size))
    );

    let found = false;
    map.eachLayer((layer) => {
      if (layer.feature && layer.getBounds && bounds.intersects(layer.getBounds())) {
        found = true;
        selectedLayersRef.current.push(layer);
        if (layer.setStyle) {
          layer.setStyle({
            color: '#ef4444',
            weight: 3,
            opacity: 1,
            fillOpacity: 0.3
          });
        }
        if (layer.bringToFront) {
          layer.bringToFront();
        }
      }
    });

    if (found && onFeatureSelect) {
      const selectedFeatures = selectedLayersRef.current.map(l => l.feature);
      onFeatureSelect(selectedFeatures);
    }
  };

  // Fonction pour sélectionner les entités dans un rectangle
  const selectFeaturesInBounds = (bounds) => {
    // Réinitialiser le style des entités précédemment sélectionnées
    selectedLayersRef.current.forEach(layer => {
      if (layer.setStyle) {
        layer.setStyle({
          color: '#3388ff',
          weight: 2,
          opacity: 0.8,
          fillOpacity: 0.2
        });
      }
    });
    selectedLayersRef.current = [];

    const selectedFeatures = [];
    const selectedIds = new Set(); // Pour éviter les doublons

    // Créer un polygone Turf.js à partir du rectangle
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    const nw = L.latLng(ne.lat, sw.lng);
    const se = L.latLng(sw.lat, ne.lng);

    const rectanglePolygon = turf.polygon([[
      [sw.lng, sw.lat],
      [se.lng, se.lat],
      [ne.lng, ne.lat],
      [nw.lng, nw.lat],
      [sw.lng, sw.lat]
    ]]);

    // Parcourir toutes les couches de la carte
    map.eachLayer((layer) => {
      if (!layer.feature) return;

      // Identifiant unique pour éviter les doublons (générique)
      const featureId = layer.feature.id ||
                       layer.feature.properties?.code_insee ||
                       layer.feature.properties?.id ||
                       layer.feature.properties?.name ||
                       layer.feature.properties?.nom ||
                       JSON.stringify(layer.feature.geometry?.coordinates?.[0] || layer.feature.properties);

      // Éviter les doublons
      if (selectedIds.has(featureId)) return;

      let isInBounds = false;

      try {
        const geom = layer.feature.geometry;
        let featureTurf;

        if (geom.type === 'Point') {
          // Pour les points
          const point = turf.point(geom.coordinates);
          isInBounds = turf.booleanPointInPolygon(point, rectanglePolygon);
        } else if (geom.type === 'Polygon') {
          // Pour les polygones, vérifier l'intersection
          featureTurf = turf.polygon(geom.coordinates);
          try {
            const intersection = turf.intersect(turf.featureCollection([featureTurf, rectanglePolygon]));
            isInBounds = intersection !== null;
          } catch (e) {
            // Fallback: vérifier si au moins un point du polygone est dans le rectangle
            const coords = geom.coordinates[0];
            for (const coord of coords) {
              const point = turf.point(coord);
              if (turf.booleanPointInPolygon(point, rectanglePolygon)) {
                isInBounds = true;
                break;
              }
            }
          }
        } else if (geom.type === 'MultiPolygon') {
          // Pour les multi-polygones
          featureTurf = turf.multiPolygon(geom.coordinates);
          try {
            const intersection = turf.intersect(turf.featureCollection([featureTurf, rectanglePolygon]));
            isInBounds = intersection !== null;
          } catch (e) {
            // Fallback
            const coords = geom.coordinates[0][0];
            for (const coord of coords) {
              const point = turf.point(coord);
              if (turf.booleanPointInPolygon(point, rectanglePolygon)) {
                isInBounds = true;
                break;
              }
            }
          }
        } else if (geom.type === 'LineString' || geom.type === 'MultiLineString') {
          // Pour les lignes, vérifier si au moins un point est dans le rectangle
          const coords = geom.type === 'LineString' ? geom.coordinates : geom.coordinates[0];
          for (const coord of coords) {
            const point = turf.point(coord);
            if (turf.booleanPointInPolygon(point, rectanglePolygon)) {
              isInBounds = true;
              break;
            }
          }
        }

        if (isInBounds) {
          selectedFeatures.push(layer.feature);
          selectedIds.add(featureId);

          // Mettre en surbrillance en rouge
          if (layer.setStyle) {
            layer.setStyle({
              color: '#ef4444',
              weight: 3,
              opacity: 1,
              fillOpacity: 0.3
            });
            selectedLayersRef.current.push(layer);
          }
        }
      } catch (error) {
        console.error('Erreur lors de la sélection:', error, layer.feature);
      }
    });

    console.log(`${selectedFeatures.length} entité(s) sélectionnée(s)`);

    if (onFeatureSelect) {
      onFeatureSelect(selectedFeatures);
    }
  };

  return null;
}

export default MapTools;
