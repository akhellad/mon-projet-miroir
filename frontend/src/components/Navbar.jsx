/**
 * Barre de navigation principale de l'application
 * Affiche le logo et les onglets de navigation entre les différentes pages
 */
function Navbar({ currentPage, onPageChange }) {
  const pages = [
    { id: 'map', label: 'Cartographie' },
    { id: 'dashboard', label: 'Tableaux de bord' },
    { id: 'layers', label: 'Gestion des couches' },
    { id: 'export', label: 'Export PDF' }
  ];

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand" onClick={() => onPageChange('map')}>
          <img
            src="/logos/Logo Naldeo Digital For Climate.png"
            alt="Naldeo Digital For Climate"
            className="navbar-logo-img"
          />
          <div className="navbar-text">
            <div className="navbar-logo">SDAEP</div>
            <div className="navbar-subtitle">Observatoire - Département de l'Ardèche</div>
          </div>
        </div>

        <div className="navbar-tabs">
          {pages.map(page => (
            <button
              key={page.id}
              className={`nav-tab ${currentPage === page.id ? 'active' : ''}`}
              onClick={() => onPageChange(page.id)}
            >
              {page.label}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
