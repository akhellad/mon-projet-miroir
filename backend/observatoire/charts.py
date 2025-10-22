"""
Module de génération de graphiques statistiques.

Utilise Matplotlib pour créer des visualisations de données géographiques
encodées en base64 pour intégration dans les rapports PDF et le frontend.
"""

import matplotlib
matplotlib.use('Agg')  # Backend sans interface graphique pour environnement serveur
import matplotlib.pyplot as plt
import io
import base64
from .models import Layer, Feature, Commune

# Configuration globale du style des graphiques
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9


def get_communes_layer():
    """
    Récupère la couche des communes depuis la base de données.

    Returns:
        Layer: Instance de la couche Communes, ou None si non trouvée
    """
    try:
        return Layer.objects.get(name='Communes')
    except Layer.DoesNotExist:
        return None


def generate_top_communes_chart():
    """
    Génère un graphique horizontal des communes les plus peuplées.

    Returns:
        str: Image PNG encodée en base64 au format data URI
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Note: La population n'est pas encore disponible dans le modèle Commune
    # Ce graphique sera fonctionnel une fois que les données de population seront importées
    names = []
    populations = []

    bars = ax.barh(names, populations, color='#1e40af', edgecolor='white', linewidth=1)
    ax.set_xlabel('Population', fontsize=10)
    ax.set_title('Top 10 communes par population', fontsize=11, fontweight='bold', pad=10)
    ax.grid(True, alpha=0.3, axis='x', linestyle='--')

    # Inverser l'ordre pour avoir la plus grande en haut
    ax.invert_yaxis()

    # Format de l'axe X sans décimales
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', ' ')))

    plt.tight_layout()

    # Convertir en base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)

    return f"data:image/png;base64,{image_base64}"


def generate_population_pie_chart():
    """
    Génère un diagramme circulaire pour la répartition par tranche de population (similaire au dashboard)
    """
    fig, ax = plt.subplots(figsize=(6, 5))

    # Note: La population n'est pas encore disponible dans le modèle Commune
    # Ce graphique sera fonctionnel une fois que les données de population seront importées
    counts = []
    labels = []

    colors = ['#1e3a8a', '#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#60a5fa', '#3b82f6']

    # Fonction pour afficher les pourcentages seulement si > 3%
    def autopct_format(pct):
        return f'{pct:.1f}%' if pct > 3 else ''

    wedges, texts, autotexts = ax.pie(
        counts,
        colors=colors[:len(counts)],
        autopct=autopct_format,
        startangle=90,
        textprops={'fontsize': 8}
    )

    # Style des pourcentages
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    # Légende à côté du graphique pour éviter les chevauchements
    ax.legend(labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)
    ax.axis('equal')
    plt.title('Répartition par tranche de population', fontsize=11, fontweight='bold', pad=10)

    plt.tight_layout()

    # Convertir en base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)

    return f"data:image/png;base64,{image_base64}"


def generate_population_distribution_bar_chart():
    """
    Génère un graphique en barres de distribution des communes par tranches (similaire au dashboard)
    """
    fig, ax = plt.subplots(figsize=(7, 4))

    # Note: La population n'est pas encore disponible dans le modèle Commune
    # Ce graphique sera fonctionnel une fois que les données de population seront importées
    counts = []
    labels = []

    colors = ['#1e3a8a', '#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe']

    bars = ax.bar(labels, counts, color=colors, edgecolor='white', linewidth=1.5)

    # Ajouter les valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Tranche de population', fontsize=10)
    ax.set_ylabel('Nombre de communes', fontsize=10)
    ax.set_title('Distribution des communes', fontsize=11, fontweight='bold', pad=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Convertir en base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)

    return f"data:image/png;base64,{image_base64}"
