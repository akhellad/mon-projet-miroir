import { useState, useMemo, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './Export.css';

/**
 * Composant d'export de fiches de synthèse PDF pour les communes
 * Permet de rechercher une commune et de générer/télécharger sa fiche PDF
 * Affiche un aperçu de la fiche avant export
 */
function Export() {
  const [communesData, setCommunesData] = useState(null);
  const [selectedCommune, setSelectedCommune] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  /**
   * Chargement initial de la liste des communes depuis l'API
   * Récupère uniquement les propriétés pour optimisation
   */
  useEffect(() => {
    const loadCommunes = async () => {
      try {
        const layersResponse = await axios.get(`${API_BASE_URL}/api/layers/`);
        const communesLayer = layersResponse.data.find(l => l.name === 'Communes');

        if (communesLayer) {
          const dataResponse = await axios.get(`${API_BASE_URL}/api/layers/${communesLayer.id}/properties/`);
          setCommunesData(dataResponse.data);
        }
      } catch (err) {
        console.error('Erreur chargement communes:', err);
      }
    };

    loadCommunes();
  }, []);

  /**
   * Filtrage des communes pour l'autocomplétion
   * Recherche insensible à la casse, triée alphabétiquement
   */
  const filteredCommunes = useMemo(() => {
    if (!communesData || !communesData.features) return [];

    return communesData.features
      .filter(f =>
        f.properties.nom.toLowerCase().includes(searchTerm.toLowerCase())
      )
      .sort((a, b) => a.properties.nom.localeCompare(b.properties.nom));
  }, [communesData, searchTerm]);

  /**
   * Gère l'export PDF de la commune sélectionnée
   * Ouvre le PDF généré dans un nouvel onglet
   */
  const handleExportPDF = () => {
    if (!selectedCommune) {
      alert('Veuillez sélectionner une commune');
      return;
    }

    const url = `${API_BASE_URL}/api/export/commune/${selectedCommune}/`;
    window.open(url, '_blank');
  };

  /**
   * Récupère les données de la commune sélectionnée
   */
  const selectedCommuneData = useMemo(() => {
    if (!selectedCommune || !communesData) return null;
    return communesData.features.find(f => f.properties.code_insee === selectedCommune);
  }, [selectedCommune, communesData]);

  return (
    <div className="export-container">
      <div className="export-header">
        <h2>Export de fiches de synthèse PDF</h2>
        <p>Sélectionnez une commune pour générer sa fiche de synthèse au format PDF</p>
      </div>

      <div className="export-content">
        <div className="export-form">
          <div className="form-group">
            <label>Rechercher une commune</label>
            <input
              type="text"
              placeholder="Tapez le nom d'une commune..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-commune-input"
            />
          </div>

          {searchTerm && filteredCommunes.length > 0 && (
            <div className="commune-list">
              {filteredCommunes.slice(0, 10).map(commune => (
                <div
                  key={commune.properties.code_insee}
                  className={`commune-item ${selectedCommune === commune.properties.code_insee ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedCommune(commune.properties.code_insee);
                    setSearchTerm(commune.properties.nom);
                  }}
                >
                  <div className="commune-name">{commune.properties.nom}</div>
                  <div className="commune-details">
                    Code INSEE: {commune.properties.code_insee} |
                    Population: {commune.properties.population || 'N/A'}
                  </div>
                </div>
              ))}
            </div>
          )}

          <button
            onClick={handleExportPDF}
            disabled={!selectedCommune}
            className="export-button"
          >
            Générer le PDF
          </button>
        </div>

        {selectedCommune && (
          <div className="preview-card">
            <h3>Aperçu de la fiche</h3>
            <iframe
              src={`${API_BASE_URL}/api/preview/commune/${selectedCommune}/`}
              className="preview-iframe"
              title="Aperçu de la fiche PDF"
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default Export;
