import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useAuth } from './AuthContext';

/**
 * Contexte global pour la gestion des couches géographiques
 * - Chargement des métadonnées et données GeoJSON des couches
 * - Mise en cache des données pour éviter les rechargements
 * - Mise à jour de la visibilité et du style
 */
const LayerContext = createContext();

export function LayerProvider({ children }) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [layers, setLayers] = useState([]);
  const [layersData, setLayersData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [activeLayerId, setActiveLayerId] = useState(null);
  const loadingRef = useRef(false);
  const lastLoadRef = useRef(0);

  /**
   * Charge les métadonnées et données GeoJSON des couches
   * Implémente un système de cache et de debounce pour optimiser les performances
   */
  const loadLayers = useCallback(async (force = false) => {
    if (loadingRef.current) return;

    // Debounce : éviter les rechargements trop fréquents
    const now = Date.now();
    if (!force && now - lastLoadRef.current < 1000) return;

    loadingRef.current = true;
    setIsLoading(true);
    lastLoadRef.current = now;

    try {
      const response = await axios.get(`${API_BASE_URL}/api/layers/`);
      const newLayers = response.data;

      setLayers(newLayers);

      // Chargement asynchrone des données GeoJSON avec mise en cache
      setLayersData(prev => {
        const newData = { ...prev };

        for (const layer of newLayers) {
          if (!newData[layer.id]) {
            console.log(`Chargement de la couche ${layer.name}...`);

            axios.get(`${API_BASE_URL}/api/layers/${layer.id}/geojson/`)
              .then(dataResponse => {
                setLayersData(current => ({ ...current, [layer.id]: dataResponse.data }));
              })
              .catch(err => {
                console.error(`Erreur chargement couche ${layer.name}:`, err);
              });
          }
        }

        // Nettoyage du cache : suppression des couches qui n'existent plus
        const layerIds = new Set(newLayers.map(l => l.id));
        const cleaned = {};

        Object.keys(newData).forEach(id => {
          if (layerIds.has(parseInt(id))) {
            cleaned[id] = newData[id];
          }
        });

        return cleaned;
      });
    } catch (err) {
      console.error('Erreur chargement couches:', err);
    } finally {
      loadingRef.current = false;
      setIsLoading(false);
    }
  }, []);

  /**
   * Chargement initial des couches au montage du composant
   * Ne charge que si l'utilisateur est authentifié
   */
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      loadLayers(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, authLoading]); // loadLayers est stable via useCallback

  /**
   * Met à jour la visibilité d'une couche dans l'API et l'état local
   */
  const updateLayerVisibility = useCallback(async (layerId, visible) => {
    try {
      await axios.patch(`${API_BASE_URL}/api/layers/${layerId}/`, { visible });
      setLayers(prev => prev.map(l => l.id === layerId ? { ...l, visible } : l));
    } catch (err) {
      console.error('Erreur mise à jour visibilité:', err);
      throw err;
    }
  }, []);

  /**
   * Met à jour le style d'une couche dans l'API et l'état local
   */
  const updateLayerStyle = useCallback(async (layerId, styleUpdates) => {
    try {
      await axios.patch(`${API_BASE_URL}/api/layers/${layerId}/`, styleUpdates);
      setLayers(prev => prev.map(l => l.id === layerId ? { ...l, ...styleUpdates } : l));
    } catch (err) {
      console.error('Erreur mise à jour style:', err);
      throw err;
    }
  }, []);

  /**
   * Réorganise les couches en mettant à jour leur ordre (z-index)
   * @param {Array} layersOrder - Tableau d'objets {id, order}
   */
  const reorderLayers = useCallback(async (layersOrder) => {
    // Mise à jour optimiste : mettre à jour l'UI immédiatement
    const orderMap = new Map(layersOrder.map(l => [l.id, l.order]));
    setLayers(prev => {
      return prev
        .map(layer => ({
          ...layer,
          order: orderMap.get(layer.id) ?? layer.order
        }))
        .sort((a, b) => (a.order || 0) - (b.order || 0)); // Tri par order croissant
    });

    // Puis synchroniser avec le backend
    try {
      await axios.post(`${API_BASE_URL}/api/layers/reorder/`, { layers: layersOrder });
    } catch (err) {
      console.error('Erreur réorganisation couches:', err);
      // En cas d'erreur, recharger les couches depuis le serveur
      loadLayers(true);
      throw err;
    }
  }, [loadLayers]);

  /**
   * Définit la couche active pour la sélection d'entités
   * @param {Number|null} layerId - ID de la couche à activer, ou null pour désactiver
   */
  const setActiveLayer = useCallback((layerId) => {
    setActiveLayerId(layerId);
  }, []);

  const value = {
    layers,
    layersData,
    isLoading,
    activeLayerId,
    loadLayers,
    updateLayerVisibility,
    updateLayerStyle,
    reorderLayers,
    setActiveLayer
  };

  return (
    <LayerContext.Provider value={value}>
      {children}
    </LayerContext.Provider>
  );
}

/**
 * Hook pour accéder au contexte des couches
 * Doit être utilisé à l'intérieur d'un LayerProvider
 */
export function useLayerContext() {
  const context = useContext(LayerContext);
  if (!context) {
    throw new Error('useLayerContext doit être utilisé dans un LayerProvider');
  }
  return context;
}
