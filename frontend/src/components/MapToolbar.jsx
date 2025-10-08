import './MapToolbar.css';

/**
 * Barre d'outils de la carte avec les différents outils interactifs
 * (navigation, sélection, mesures)
 */
function MapToolbar({ onToolSelect, activeTool }) {
  const tools = [
    { id: 'pan', icon: '/icons/main.png', title: 'Outil de navigation (Pan)' },
    { id: 'select', icon: '/icons/robinet.png', title: 'Sélection simple au clic' },
    { id: 'selectBox', icon: '/icons/forme.png', title: 'Sélection par rectangle' },
    { id: 'measure', icon: '/icons/regle.png', title: 'Mesurer une distance' },
    { id: 'measureArea', icon: '/icons/hexagone.png', title: 'Mesurer une surface' },
  ];

  return (
    <div className="map-toolbar">
      {tools.map(tool => (
        <button
          key={tool.id}
          className={`toolbar-btn ${activeTool === tool.id ? 'active' : ''}`}
          onClick={() => onToolSelect(tool.id)}
          title={tool.title}
        >
          <img src={tool.icon} alt={tool.title} className="toolbar-icon" />
        </button>
      ))}
    </div>
  );
}

export default MapToolbar;
