"""
Module de modèles pour l'Observatoire SDAEP.

Ce fichier __init__.py importe tous les modèles de l'application
pour les rendre accessibles à Django.

Organisation :
- Modèles de base (géographie, infrastructure) : models/base.py
- Modèles temporels (performances annuelles) : models/temporelles.py
- Modèles de qualité : models/qualite.py
- Modèles de bilans et actions : models/bilans.py
- Modèles de tarification : models/tarification.py
- Modèles de référentiels : models/referentiels.py
"""

# Modèles de base (géographie et infrastructure)
from .base import (
    Layer,
    Feature,
    Arrondissement,
    Canton,
    Commune,
    UGE,
    UDI,
    Captage,
    CommuneUGE,
    UGECaptage,
    StationTraitement,
    StationPompage,
    Reservoir,
    MelangeCaptage,
    MelangeCaptageDetail,
    Interconnexion,
)

# Modèles temporels (performances annuelles)
from .temporelles import (
    UGEPerformanceAnnuelle,
    CaptagePerformanceAnnuelle,
    InterconnexionVolumeAnnuel,
    CommuneDonneesAnnuelles,
    CommuneTourismeAnnuel,
    UGEPatrimoineAnnuel,
)

# Modèles de qualité de l'eau
from .qualite import (
    ParametreQualite,
    AnalyseQualite,
    UGEConformiteAnnuelle,
)

# Modèles de bilans et plans d'action
from .bilans import (
    BilanBesoinsRessources,
    VulnerabiliteUGE,
    PlanAction,
)

# Modèles de tarification
from .tarification import (
    GrilleTarifaire,
    TrancheTarifaire,
)

# Modèles de référentiels et métadonnées
from .referentiels import (
    SourceDonnees,
    ImportHistorique,
    Glossaire,
    Configuration,
)

__all__ = [
    # Modèles de base
    'Layer',
    'Feature',
    'Arrondissement',
    'Canton',
    'Commune',
    'UGE',
    'UDI',
    'Captage',
    'CommuneUGE',
    'UGECaptage',
    'StationTraitement',
    'StationPompage',
    'Reservoir',
    'MelangeCaptage',
    'MelangeCaptageDetail',
    'Interconnexion',

    # Modèles temporels
    'UGEPerformanceAnnuelle',
    'CaptagePerformanceAnnuelle',
    'InterconnexionVolumeAnnuel',
    'CommuneDonneesAnnuelles',
    'CommuneTourismeAnnuel',
    'UGEPatrimoineAnnuel',

    # Modèles de qualité
    'ParametreQualite',
    'AnalyseQualite',
    'UGEConformiteAnnuelle',

    # Modèles de bilans
    'BilanBesoinsRessources',
    'VulnerabiliteUGE',
    'PlanAction',

    # Modèles de tarification
    'GrilleTarifaire',
    'TrancheTarifaire',

    # Modèles de référentiels
    'SourceDonnees',
    'ImportHistorique',
    'Glossaire',
    'Configuration',
]
