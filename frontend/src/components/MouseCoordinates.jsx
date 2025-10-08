import { useMap } from 'react-leaflet';
import { useState, useEffect } from 'react';
import proj4 from 'proj4';
import './MouseCoordinates.css';

/**
 * Composant pour afficher les coordonnées de la souris en Lambert 93
 */
function MouseCoordinates() {
  const map = useMap();
  const [coordinates, setCoordinates] = useState(null);

  useEffect(() => {
    // Définir la projection Lambert 93 (EPSG:2154)
    proj4.defs('EPSG:2154', '+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs');

    const handleMouseMove = (e) => {
      const { lat, lng } = e.latlng;

      // Convertir WGS84 (lat/lng) vers Lambert 93
      const [x, y] = proj4('EPSG:4326', 'EPSG:2154', [lng, lat]);

      setCoordinates({
        x: Math.round(x),
        y: Math.round(y),
        lat: lat.toFixed(5),
        lng: lng.toFixed(5)
      });
    };

    const handleMouseOut = () => {
      setCoordinates(null);
    };

    map.on('mousemove', handleMouseMove);
    map.on('mouseout', handleMouseOut);

    return () => {
      map.off('mousemove', handleMouseMove);
      map.off('mouseout', handleMouseOut);
    };
  }, [map]);

  if (!coordinates) return null;

  return (
    <div className="mouse-coordinates">
      <div className="coordinate-item">
        <span className="coordinate-value">X: {coordinates.x.toLocaleString('fr-FR')} m</span>
        <span className="coordinate-separator">|</span>
        <span className="coordinate-value">Y: {coordinates.y.toLocaleString('fr-FR')} m</span>
      </div>
      <div className="coordinate-item coordinate-secondary">
        <span className="coordinate-label">WGS84:</span>
        <span className="coordinate-value">{coordinates.lat}° N, {coordinates.lng}° E</span>
      </div>
    </div>
  );
}

export default MouseCoordinates;
