import { useMap } from 'react-leaflet';
import { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

/**
 * Composant pour afficher l'échelle de la carte
 */
function MapScale() {
  const map = useMap();

  useEffect(() => {
    // Créer le contrôle d'échelle
    const scaleControl = L.control.scale({
      position: 'bottomright',
      metric: true,
      imperial: false,
      maxWidth: 200
    });

    // Ajouter le contrôle à la carte
    scaleControl.addTo(map);

    // Nettoyer lors du démontage
    return () => {
      scaleControl.remove();
    };
  }, [map]);

  return null;
}

export default MapScale;
