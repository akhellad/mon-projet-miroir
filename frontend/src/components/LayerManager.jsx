import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './LayerManager.css';

/**
 * Gestionnaire de couches géographiques
 * - Import de shapefiles (fichiers ZIP)
 * - Gestion de la visibilité et suppression des couches
 * - Configuration du style, SRID et champ identifiant
 */
function LayerManager() {
  const [layers, setLayers] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    file: null,
    name: '',
    description: '',
    identifier_field: 'id',
    style_color: '#3388ff',
    srid: 'auto'
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  /**
   * Chargement initial de la liste des couches
   */
  useEffect(() => {
    loadLayers();
  }, []);

  /**
   * Récupère la liste des couches depuis l'API
   */
  const loadLayers = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/layers/`);
      setLayers(response.data);
    } catch (err) {
      console.error('Erreur chargement couches:', err);
    }
  };

  /**
   * Gère la sélection d'un fichier et pré-remplit le nom
   */
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setUploadForm({ ...uploadForm, file });

    if (file && !uploadForm.name) {
      const fileName = file.name.replace('.zip', '');
      setUploadForm({ ...uploadForm, file, name: fileName });
    }
  };

  /**
   * Gère l'import d'un shapefile vers l'API
   */
  const handleUpload = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!uploadForm.file) {
      setError('Veuillez sélectionner un fichier ZIP');
      return;
    }

    if (!uploadForm.name) {
      setError('Veuillez donner un nom à la couche');
      return;
    }

    setUploading(true);

    const formData = new FormData();
    formData.append('file', uploadForm.file);
    formData.append('name', uploadForm.name);
    formData.append('description', uploadForm.description);
    formData.append('identifier_field', uploadForm.identifier_field);
    formData.append('style_color', uploadForm.style_color);

    // Envoyer le SRID seulement s'il n'est pas en mode 'auto'
    if (uploadForm.srid !== 'auto') {
      formData.append('force_srid', uploadForm.srid);
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/upload-shapefile/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setSuccess(`Couche "${response.data.name}" importée avec succès ! (${response.data.feature_count} entités)`);

      // Réinitialiser le formulaire
      setUploadForm({
        file: null,
        name: '',
        description: '',
        identifier_field: 'id',
        style_color: '#3388ff',
        srid: 'auto'
      });
      document.getElementById('file-input').value = '';

      // Recharger la liste
      loadLayers();

    } catch (err) {
      setError(err.response?.data?.error || 'Erreur lors de l\'import du shapefile');
      console.error('Erreur upload:', err);
    } finally {
      setUploading(false);
    }
  };

  const toggleVisibility = async (layer) => {
    try {
      await axios.patch(`${API_BASE_URL}/api/layers/${layer.id}/`, {
        visible: !layer.visible
      });
      loadLayers();
    } catch (err) {
      console.error('Erreur toggle visibilité:', err);
    }
  };

  const deleteLayer = async (layer) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer la couche "${layer.name}" ?`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/layers/${layer.id}/`);
      setSuccess(`Couche "${layer.name}" supprimée`);
      loadLayers();
    } catch (err) {
      setError('Erreur lors de la suppression');
      console.error('Erreur suppression:', err);
    }
  };

  return (
    <div className="layer-manager">
      <div className="layer-manager-header">
        <div className="header-content">
          <div>
            <h2>Gestionnaire de couches</h2>
            <p>Importez et gérez vos couches géographiques</p>
          </div>
          <button
            className="btn-primary"
            onClick={() => document.getElementById('file-input').click()}
          >
            + Ajouter une couche
          </button>
        </div>
      </div>

      {/* Formulaire d'import (masqué) */}
      <div className={`upload-panel ${uploadForm.file ? 'visible' : ''}`}>
        <div className="upload-header">
          <h3>Importer un Shapefile</h3>
          <button
            className="btn-close"
            onClick={() => {
              setUploadForm({
                file: null,
                name: '',
                description: '',
                identifier_field: 'id',
                style_color: '#3388ff',
                srid: 'auto'
              });
              document.getElementById('file-input').value = '';
            }}
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleUpload} className="upload-form">
          <input
            id="file-input"
            type="file"
            accept=".zip"
            onChange={handleFileChange}
            disabled={uploading}
            style={{ display: 'none' }}
          />

          {uploadForm.file && (
            <div className="file-info">
              <span className="file-icon">📦</span>
              <span className="file-name">{uploadForm.file.name}</span>
            </div>
          )}

          <div className="form-grid">
            <div className="form-group">
              <label>Nom de la couche *</label>
              <input
                type="text"
                value={uploadForm.name}
                onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                placeholder="Ex: Captages, Réseaux..."
                disabled={uploading}
              />
            </div>

            <div className="form-group">
              <label>Champ identifiant</label>
              <input
                type="text"
                value={uploadForm.identifier_field}
                onChange={(e) => setUploadForm({ ...uploadForm, identifier_field: e.target.value })}
                placeholder="id"
                disabled={uploading}
              />
            </div>

            <div className="form-group">
              <label>Couleur</label>
              <input
                type="color"
                value={uploadForm.style_color}
                onChange={(e) => setUploadForm({ ...uploadForm, style_color: e.target.value })}
                disabled={uploading}
              />
            </div>

            <div className="form-group">
              <label>Système de coordonnées (SRID)</label>
              <select
                value={uploadForm.srid}
                onChange={(e) => setUploadForm({ ...uploadForm, srid: e.target.value })}
                disabled={uploading}
              >
                <option value="auto">Auto-détection</option>
                <option value="2154">EPSG:2154 (Lambert 93)</option>
                <option value="4326">EPSG:4326 (WGS 84)</option>
                <option value="3857">EPSG:3857 (Web Mercator)</option>
                <option value="2972">EPSG:2972 (UTM 22N - Antilles)</option>
                <option value="32620">EPSG:32620 (UTM 20N)</option>
              </select>
            </div>

            <div className="form-group full-width">
              <label>Description (optionnel)</label>
              <textarea
                value={uploadForm.description}
                onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                placeholder="Description de la couche..."
                rows="2"
                disabled={uploading}
              />
            </div>
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={uploading}>
              {uploading ? 'Import en cours...' : 'Importer'}
            </button>
          </div>
        </form>
      </div>

      {/* Table des couches */}
      <div className="layers-table-container">
        <div className="table-header">
          <h3>Couches ({layers.length})</h3>
        </div>

        {layers.length === 0 ? (
          <div className="no-layers">
            <div className="no-layers-icon">🗺️</div>
            <p>Aucune couche importée</p>
            <p className="no-layers-hint">Cliquez sur "Ajouter une couche" pour commencer</p>
          </div>
        ) : (
          <table className="layers-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th style={{ width: '50px' }}>Couleur</th>
                <th>Nom</th>
                <th>Type</th>
                <th>Entités</th>
                <th>SRID</th>
                <th>Identifiant</th>
                <th>Date de création</th>
                <th style={{ width: '120px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {layers.map(layer => (
                <tr key={layer.id} className={layer.visible ? '' : 'layer-hidden'}>
                  <td>
                    <input
                      type="checkbox"
                      checked={layer.visible}
                      onChange={() => toggleVisibility(layer)}
                      title={layer.visible ? 'Masquer' : 'Afficher'}
                    />
                  </td>
                  <td>
                    <div
                      className="layer-color-preview"
                      style={{ backgroundColor: layer.style_color }}
                    />
                  </td>
                  <td className="layer-name-cell">
                    <strong>{layer.name}</strong>
                    {layer.description && (
                      <div className="layer-description-hint">{layer.description}</div>
                    )}
                  </td>
                  <td>
                    <span className="badge badge-geometry">
                      {layer.geometry_type}
                    </span>
                  </td>
                  <td>{layer.feature_count.toLocaleString('fr-FR')}</td>
                  <td>
                    <span className="badge badge-srid">EPSG:{layer.srid}</span>
                  </td>
                  <td><code>{layer.identifier_field}</code></td>
                  <td>{new Date(layer.created_at).toLocaleDateString('fr-FR')}</td>
                  <td>
                    <div className="table-actions">
                      <button
                        onClick={() => deleteLayer(layer)}
                        className="btn-table-action btn-danger"
                        title="Supprimer"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default LayerManager;
