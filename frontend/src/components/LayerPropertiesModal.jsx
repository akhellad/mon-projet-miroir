import { useState } from 'react';
import { createPortal } from 'react-dom';
import './LayerPropertiesModal.css';

/**
 * Modal de configuration des propriétés d'une couche
 * Permet de modifier le nom et le style (couleur, épaisseur, opacité) en temps réel
 */
function LayerPropertiesModal({ layer, onClose, onUpdate }) {
  const [formData, setFormData] = useState({
    name: layer.name,
    style_color: layer.style_color,
    style_weight: layer.style_weight,
    style_opacity: layer.style_opacity,
    style_fill_opacity: layer.style_fill_opacity
  });

  const handleChange = (field, value) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    // Mise à jour en temps réel
    onUpdate(layer.id, { [field]: value });
  };

  const handleClose = () => {
    onClose();
  };

  return createPortal(
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Propriétés de la couche</h3>
          <button className="modal-close-btn" onClick={handleClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="property-section">
            <h4>Informations</h4>
            <div className="property-item">
              <label>Nom</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="property-input"
                placeholder="Nom de la couche"
              />
            </div>
            <div className="property-item">
              <label>Type de géométrie</label>
              <div className="property-value">{layer.geometry_type}</div>
            </div>
            <div className="property-item">
              <label>SRID</label>
              <div className="property-value">{layer.srid}</div>
            </div>
            <div className="property-item">
              <label>Nombre d'entités</label>
              <div className="property-value">{layer.feature_count}</div>
            </div>
            {layer.description && (
              <div className="property-item">
                <label>Description</label>
                <div className="property-value">{layer.description}</div>
              </div>
            )}
          </div>

          <div className="property-section">
            <h4>Style</h4>

            <div className="property-item">
              <label>Couleur</label>
              <div className="property-control">
                <input
                  type="color"
                  value={formData.style_color}
                  onChange={(e) => handleChange('style_color', e.target.value)}
                  className="color-picker"
                />
                <span className="color-value">{formData.style_color}</span>
              </div>
            </div>

            <div className="property-item">
              <label>Épaisseur du contour</label>
              <div className="property-control">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={formData.style_weight}
                  onChange={(e) => handleChange('style_weight', parseInt(e.target.value))}
                  className="range-slider"
                />
                <span className="range-value">{formData.style_weight} px</span>
              </div>
            </div>

            <div className="property-item">
              <label>Opacité du contour</label>
              <div className="property-control">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={formData.style_opacity * 100}
                  onChange={(e) => handleChange('style_opacity', e.target.value / 100)}
                  className="range-slider"
                />
                <span className="range-value">{Math.round(formData.style_opacity * 100)}%</span>
              </div>
            </div>

            <div className="property-item">
              <label>Opacité du remplissage</label>
              <div className="property-control">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={formData.style_fill_opacity * 100}
                  onChange={(e) => handleChange('style_fill_opacity', e.target.value / 100)}
                  className="range-slider"
                />
                <span className="range-value">{Math.round(formData.style_fill_opacity * 100)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}

export default LayerPropertiesModal;
