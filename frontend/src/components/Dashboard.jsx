import { useMemo, useEffect, useState } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './Dashboard.css';

/**
 * Composant de tableau de bord affichant les statistiques des communes
 * Génère automatiquement des graphiques (camembert, barres) à partir des données de population
 * Les données sont récupérées depuis l'API et affichées avec des animations
 */
function Dashboard() {
  const [communesData, setCommunesData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showCharts, setShowCharts] = useState(false);

  /**
   * Chargement initial des données des communes depuis l'API
   * Récupère uniquement les propriétés (sans géométries) pour optimisation
   */
  useEffect(() => {
    const loadCommunes = async () => {
      setIsLoading(true);
      try {
        const layersResponse = await axios.get(`${API_BASE_URL}/api/layers/`);
        const communesLayer = layersResponse.data.find(l => l.name === 'Communes');

        if (communesLayer) {
          const dataResponse = await axios.get(`${API_BASE_URL}/api/layers/${communesLayer.id}/properties/`);

          // Délai artificiel pour permettre l'affichage des animations
          await new Promise(resolve => setTimeout(resolve, 500));

          setCommunesData(dataResponse.data);
        } else {
          console.error('Couche Communes non trouvée');
        }
      } catch (err) {
        console.error('Erreur chargement communes:', err);
      } finally {
        setIsLoading(false);
        setTimeout(() => setShowCharts(true), 100);
      }
    };

    loadCommunes();
  }, []);

  /**
   * Calcul des statistiques globales sur les communes
   * - Nombre total de communes
   * - Population totale, moyenne, min et max
   */
  const stats = useMemo(() => {
    if (!communesData || !communesData.features) {
      return {
        totalCommunes: 0,
        totalPopulation: 0,
        avgPopulation: 0,
        maxPopulation: 0,
        minPopulation: 0
      };
    }

    const populations = communesData.features
      .map(f => f.properties?.population || 0)
      .filter(p => p > 0);

    const total = populations.reduce((acc, p) => acc + p, 0);

    return {
      totalCommunes: communesData.features.length,
      totalPopulation: total,
      avgPopulation: Math.round(total / populations.length),
      maxPopulation: Math.max(...populations),
      minPopulation: Math.min(...populations)
    };
  }, [communesData]);

  /**
   * Calcul de la répartition des communes par tranches de population
   * Utilisé pour les graphiques camembert et barres
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

    return ranges.map(r => ({ name: r.name, communes: r.count })).reverse();
  }, [communesData]);

  /**
   * Extraction du top 10 des communes les plus peuplées
   */
  const topCommunes = useMemo(() => {
    if (!communesData || !communesData.features) return [];

    return communesData.features
      .filter(f => f.properties.population > 0)
      .sort((a, b) => b.properties.population - a.properties.population)
      .slice(0, 10)
      .map(f => ({
        name: f.properties.nom,
        population: f.properties.population
      }));
  }, [communesData]);

  // Palette de couleurs pour les graphiques (dégradé de bleus)
  const COLORS = ['#1e3a8a', '#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#60a5fa', '#3b82f6'];

  // Affichage du loader pendant le chargement
  if (isLoading) {
    return (
      <div className="dashboard">
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

      {/* Cards statistiques */}
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

      {/* Graphiques */}
      <div className="charts-grid">
        {/* Répartition par tranche de population */}
        <div className="chart-card">
          <h3>Répartition par tranche de population</h3>
          {showCharts && (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={populationRanges}
                  dataKey="communes"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) => `${entry.name}: ${entry.communes}`}
                  isAnimationActive={true}
                  animationBegin={0}
                  animationDuration={1000}
                  animationEasing="ease-out"
                >
                  {populationRanges.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top 10 communes */}
        <div className="chart-card chart-card-wide">
          <h3>Top 10 communes par population</h3>
          {showCharts && (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topCommunes}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} style={{ fontSize: '12px' }} />
                <YAxis style={{ fontSize: '12px' }} />
                <Tooltip />
                <Bar
                  dataKey="population"
                  fill="#1e40af"
                  radius={[8, 8, 0, 0]}
                  isAnimationActive={true}
                  animationBegin={200}
                  animationDuration={1000}
                  animationEasing="ease-out"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Distribution des communes par tranche */}
        <div className="chart-card chart-card-wide">
          <h3>Distribution des communes</h3>
          {showCharts && (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={populationRanges}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" style={{ fontSize: '12px' }} />
                <YAxis style={{ fontSize: '12px' }} />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="communes"
                  fill="#3b82f6"
                  name="Nombre de communes"
                  radius={[8, 8, 0, 0]}
                  isAnimationActive={true}
                  animationBegin={400}
                  animationDuration={1000}
                  animationEasing="ease-out"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
