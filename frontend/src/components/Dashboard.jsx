// frontend/src/components/Dashboard.jsx
import { useMemo, useEffect, useState, useCallback, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useLayerContext } from '../contexts/LayerContext';
import './Dashboard.css';
import D3BarChart from './D3BarChart';
import D3PieChart from './D3PieChart';

/**
 * Composant de tableau de bord affichant les statistiques des communes
 * Génère automatiquement des graphiques (camembert, barres) à partir des données de population avec D3.js
 * Utilise le LayerContext pour optimiser le chargement des données (cache).
 */
function Dashboard() {
  const { layers, layersData } = useLayerContext();
  const [communesData, setCommunesData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const hasLoadedRef = useRef(false); // Tracker pour éviter les rechargements

  /**
   * Chargement optimisé des données depuis le LayerContext
   * Utilise le cache existant plutôt que de refaire des appels API
   * Ne se charge qu'une seule fois grâce au ref
   */
  useEffect(() => {
    // Ne charger qu'une seule fois
    if (hasLoadedRef.current) return;

    const loadCommunes = async () => {
      setIsLoading(true);
      try {
        // Trouver la couche Communes dans le contexte
        const communesLayer = layers.find(l => l.name === 'Communes');

        if (communesLayer) {
          // Vérifier si les données sont déjà en cache
          const cachedData = layersData[communesLayer.id];

          if (cachedData) {
            // Utiliser les données du cache (instantané)
            setCommunesData(cachedData);
            hasLoadedRef.current = true;
            setIsLoading(false);
          } else {
            // Sinon, charger depuis l'API
            const dataResponse = await axios.get(`${API_BASE_URL}/api/layers/${communesLayer.id}/geojson/`);
            setCommunesData(dataResponse.data);
            hasLoadedRef.current = true;
            setIsLoading(false);
          }
        } else if (layers.length > 0) {
          // Les layers sont chargés mais pas de couche Communes
          console.error('Couche Communes non trouvée');
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Erreur chargement communes:', err);
        setIsLoading(false);
      }
    };

    // Attendre que les layers soient chargés
    if (layers.length > 0) {
      loadCommunes();
    }
  }, [layers, layersData]);

  /**
   * Calcul des statistiques globales sur les communes
   * (Pas de changement ici)
   */
  const stats = useMemo(() => {
    if (!communesData || !communesData.features) {
      return { totalCommunes: 0, totalPopulation: 0, avgPopulation: 0, maxPopulation: 0, minPopulation: 0 };
    }
    const populations = communesData.features.map(f => f.properties?.population || 0).filter(p => p > 0);
    const total = populations.reduce((acc, p) => acc + p, 0);
    const count = populations.length > 0 ? populations.length : 1;
    return {
      totalCommunes: communesData.features.length,
      totalPopulation: total,
      avgPopulation: Math.round(total / count),
      maxPopulation: populations.length > 0 ? Math.max(...populations) : 0,
      minPopulation: populations.length > 0 ? Math.min(...populations) : 0
    };
  }, [communesData]);

  /**
   * Calcul de la répartition des communes par tranches de population
   * (Pas de changement ici, ces données seront passées aux composants D3)
   */
  const populationRanges = useMemo(() => {
    if (!communesData || !communesData.features) return [];
    const ranges = [
      { name: '< 200', min: 0, max: 200, count: 0 },
      { name: '200-500', min: 200, max: 500, count: 0 },
      { name: '500-1000', min: 500, max: 1000, count: 0 },
      { name: '1000-2000', min: 1000, max: 2000, count: 0 },
      { name: '2000-3000', min: 2000, max: 3000, count: 0 },
      { name: '3000-5000', min: 3000, max: 5000, count: 0 },
      { name: '5000-10000', min: 5000, max: 10000, count: 0 },
      { name: '> 10000', min: 10000, max: Infinity, count: 0 }
    ];
    communesData.features.forEach(feature => {
      const pop = feature.properties.population || 0;
      const range = ranges.find(r => pop >= r.min && pop < r.max);
      if (range) range.count++;
    });
    // On garde l'ordre croissant pour l'axe X du bar chart de distribution
    return ranges.map(r => ({ name: r.name, communes: r.count }));
  }, [communesData]);

  /**
   * Extraction du top 10 des communes les plus peuplées
   * (Pas de changement ici, ces données seront passées au composant D3)
   */
  const topCommunes = useMemo(() => {
    if (!communesData || !communesData.features) return [];
    return communesData.features
      .filter(f => f.properties.population > 0)
      .sort((a, b) => b.properties.population - a.properties.population)
      .slice(0, 10)
      .map(f => ({ name: f.properties.nom, population: f.properties.population }));
  }, [communesData]);

  // Fonctions de formatage stables pour éviter les re-renders des graphiques D3
  const topCommunesTooltipFormat = useCallback((d) =>
    `<strong>${d.name}</strong><br/>${d.population.toLocaleString('fr-FR')} habitants`,
    []
  );

  const distributionTooltipFormat = useCallback((d) =>
    `<strong>${d.name} habitants</strong><br/>${d.communes} commune${d.communes > 1 ? 's' : ''}`,
    []
  );

  // Palette de couleurs moderne et harmonieuse
  const COLORS = useMemo(() => [
    '#375B6A', // Bleu foncé principal
    '#38ABAE', // Turquoise
    '#57CC99', // Vert clair
    '#2D6A6A', // Vert-bleu foncé
    '#4DB8BB', // Turquoise clair
    '#6FD9A3', // Vert menthe
    '#1E4A52', // Bleu très foncé
    '#80DEEA', // Cyan clair
  ], []);

  // Affichage du loader pendant le chargement
  if (isLoading) {
    return (
      <div className="dashboard">
        {/* ... (code du loader inchangé) ... */}
         <div className="dashboard-header">
           <h2>Tableaux de bord</h2>
           <p>Vue d'ensemble des communes de l'Ardèche</p>
         </div>
         <div className="dashboard-loading">
           <div className="loading-spinner"></div>
           <p>Chargement des données...</p>
         </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Tableaux de bord</h2>
        <p>Vue d'ensemble des communes de l'Ardèche</p>
      </div>

      {/* Cards statistiques (inchangées) */}
      <div className="stats-grid">
         <div className="stat-card">
           <div className="stat-card-label">Communes</div>
           <div className="stat-card-value">{stats.totalCommunes}</div>
         </div>
         <div className="stat-card">
           <div className="stat-card-label">Population totale</div>
           <div className="stat-card-value">{stats.totalPopulation.toLocaleString('fr-FR')}</div>
         </div>
         <div className="stat-card">
           <div className="stat-card-label">Population moyenne</div>
           <div className="stat-card-value">{stats.avgPopulation.toLocaleString('fr-FR')}</div>
         </div>
         <div className="stat-card">
           <div className="stat-card-label">Population max</div>
           <div className="stat-card-value">{stats.maxPopulation.toLocaleString('fr-FR')}</div>
         </div>
      </div>

      {/* Graphiques avec D3 */}
      <div className="charts-grid">
        {/* Répartition par tranche de population */}
        <div className="chart-card">
          <h3>Répartition par tranche de population</h3>
          {populationRanges.length > 0 ? (
            <D3PieChart
              data={populationRanges.filter(d => d.communes > 0)} // Ne passe que les tranches non vides
              valueField="communes"
              nameField="name"
              colors={COLORS}
              width={400}
              height={300}
            />
          ) : (
            <p>Données non disponibles pour ce graphique.</p>
          )}
        </div>

        {/* Top 10 communes */}
        <div className="chart-card chart-card-wide">
          <h3>Top 10 communes par population</h3>
          {topCommunes.length > 0 ? (
            <D3BarChart
              data={topCommunes}
              xField="name"
              yField="population"
              yAxisLabel="Population"
              tooltipFormat={topCommunesTooltipFormat}
              color="#38ABAE"
              width={800}
              height={350}
              rotateXLabels={true}
            />
           ) : (
            <p>Données non disponibles pour ce graphique.</p>
          )}
        </div>

        {/* Distribution des communes par tranche */}
        <div className="chart-card chart-card-wide">
          <h3>Distribution des communes</h3>
          {populationRanges.length > 0 ? (
            <D3BarChart
              data={populationRanges.filter(d => d.communes > 0)}
              xField="name"
              yField="communes"
              xAxisLabel="Tranche de population"
              yAxisLabel="Nombre de communes"
              tooltipFormat={distributionTooltipFormat}
              color="#57CC99"
              width={800}
              height={350}
              rotateXLabels={false}
            />
          ) : (
            <p>Données non disponibles pour ce graphique.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;