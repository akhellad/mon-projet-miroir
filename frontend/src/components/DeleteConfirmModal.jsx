import './UserManagement.css';

/**
 * Modal de confirmation de suppression d'utilisateur
 *
 * Props:
 * - user: Utilisateur à supprimer
 * - onConfirm: Callback pour confirmer la suppression
 * - onClose: Callback pour annuler
 */
const DeleteConfirmModal = ({ user, onConfirm, onClose }) => {
  // Fermer le modal sur clic en dehors
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal" style={{ maxWidth: '500px' }}>
        {/* Header */}
        <div className="modal-header">
          <h3>Confirmer la suppression</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          <p style={{ fontSize: '15px', color: '#475569', lineHeight: '1.6' }}>
            Êtes-vous sûr de vouloir supprimer l'utilisateur{' '}
            <strong>{user.username}</strong> ?
          </p>

          {user.first_name && user.last_name && (
            <p style={{ fontSize: '14px', color: '#64748b', marginTop: '8px' }}>
              {user.first_name} {user.last_name}
              {user.email && ` (${user.email})`}
            </p>
          )}

          <div
            style={{
              marginTop: '20px',
              padding: '16px',
              background: '#fee2e2',
              borderRadius: '8px',
              borderLeft: '4px solid #dc2626'
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: '13px',
                color: '#991b1b',
                fontWeight: '500'
              }}
            >
              ⚠️ Cette action est irréversible. Toutes les données associées à cet
              utilisateur seront définitivement supprimées.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Annuler
          </button>
          <button type="button" className="btn-danger" onClick={onConfirm}>
            Supprimer définitivement
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmModal;
