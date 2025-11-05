"""
Modèles de données temporelles pour l'Observatoire SDAEP.

SECTION 4 : DONNÉES TEMPORELLES (PERFORMANCES ANNUELLES)

Ces modèles stockent les données de performance et d'exploitation par année.
Ils constituent le cœur de l'observatoire pour le suivi dans le temps.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

# Les modèles de base sont dans le fichier models.py du répertoire parent
# Django les chargera automatiquement via les ForeignKey avec des chaînes de caractères
# On utilisera donc 'observatoire.UGE' au lieu d'importer directement


class UGEPerformanceAnnuelle(models.Model):
    """
    TABLE CENTRALE : Tous les indicateurs de performance annuels par UGE.

    Sources multiples :
      - SISPEA (feuille "collectivités") : données nationales officielles
      - SDAEP 2015 (fichiers Phase 1) : données historiques
      - Collecte terrain 2025 : données actualisées
    Utilité : Alimenter les tableaux de bord, graphiques d'évolution, comparaisons.
    Granularité : 1 ligne = 1 UGE × 1 année.
    """

    SOURCE_DONNEES_CHOICES = [
        ('SISPEA', 'SISPEA'),
        ('SDAEP_2015', 'SDAEP 2015'),
        ('COLLECTE_2025', 'Collecte terrain 2025'),
        ('ESTIME', 'Estimé'),
        ('CALCULE', 'Calculé'),
    ]

    FIABILITE_CHOICES = [
        ('HAUTE', 'Haute'),
        ('MOYENNE', 'Moyenne'),
        ('FAIBLE', 'Faible'),
        ('INCONNUE', 'Inconnue'),
    ]

    uge = models.ForeignKey(
        'observatoire.UGE',
        on_delete=models.CASCADE,
        related_name='performances_annuelles',
        verbose_name="UGE"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    # POPULATION ET USAGERS
    population_totale = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Population totale"
    )
    population_desservie = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Population desservie"
    )
    nb_abonnes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre d'abonnés"
    )
    nb_branchements = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de branchements"
    )
    nb_habitants_par_branchement = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Nombre d'habitants par branchement"
    )

    # VOLUMES (en m³/an)
    volume_produit = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume produit (m³/an)"
    )
    volume_achete = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume acheté (m³/an)"
    )
    volume_vendu = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume vendu (m³/an)"
    )
    volume_mis_en_distribution = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume mis en distribution (m³/an)"
    )
    volume_consomme = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume consommé (m³/an)"
    )
    volume_exporte = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume exporté (m³/an)"
    )
    volume_comptabilise = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume comptabilisé (m³/an)"
    )
    volume_non_comptabilise = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume non comptabilisé (m³/an)"
    )

    # VOLUMES MENSUELS ET JOURNALIERS (pointes)
    volume_pointe_mois_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume mois de pointe (m³)"
    )
    mois_pointe = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Mois de pointe",
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    volume_pointe_jour_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume jour de pointe (m³)"
    )

    # RENDEMENT ET PERTES
    rendement_reseau = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Rendement du réseau (%)",
        help_text="Rendement = (Volume consommé / Volume mis en distribution) × 100. Objectif national : > 85%.",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    indice_lineaire_perte = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Indice linéaire de perte (m³/j/km)",
        help_text="ILP = Pertes / Linéaire réseau. Indicateur complémentaire au rendement, indépendant de la consommation."
    )
    taux_perte = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de perte (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    # PRIX (pour 120 m³/an = consommation type)
    prix_eau_120m3_ttc = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Prix de l'eau pour 120 m³ TTC (€)"
    )
    part_fixe_abonnement = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Part fixe abonnement (€)"
    )
    part_variable_m3 = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Part variable (€/m³)"
    )

    # QUALITÉ EAU
    taux_conformite_bacterio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de conformité bactériologique (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    taux_conformite_physico_chimique = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de conformité physico-chimique (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    nb_prelevements_bacterio = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de prélèvements bactériologiques"
    )
    nb_prelevements_physico = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de prélèvements physico-chimiques"
    )

    # PATRIMOINE
    lineaire_reseau_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire réseau (km)"
    )
    lineaire_adduction_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire adduction (km)"
    )
    lineaire_distribution_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire distribution (km)"
    )
    taux_renouvellement_reseau = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de renouvellement réseau (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    lineaire_renouvele_km = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire renouvelé (km)"
    )

    # INDICATEURS AVANCÉS
    indice_connaissance_gestion = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name="Indice de connaissance et gestion"
    )
    indice_protection_ressource = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Indice de protection ressource",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    taux_impaye = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux d'impayés (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    # MÉTADONNÉES
    source_donnees = models.CharField(
        max_length=50,
        choices=SOURCE_DONNEES_CHOICES,
        verbose_name="Source des données",
        help_text="Source : SISPEA_2023, SDAEP_2015, Collecte_2025, Estimé, Calculé"
    )
    completude = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Complétude (%)",
        help_text="Pourcentage de champs renseignés (0-100%). Permet de juger la qualité de la donnée.",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    fiabilite = models.CharField(
        max_length=20,
        choices=FIABILITE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Fiabilité"
    )

    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'uge_performances_annuelles'
        verbose_name = "Performance annuelle UGE"
        verbose_name_plural = "Performances annuelles UGE"
        unique_together = [['uge', 'annee']]
        ordering = ['-annee', 'uge__nom_uge']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['annee']),
            models.Index(fields=['uge', 'annee']),
            models.Index(fields=['source_donnees']),
        ]

    def __str__(self):
        return f"{self.uge.nom_uge} - {self.annee}"


class CaptagePerformanceAnnuelle(models.Model):
    """
    Données de production annuelles par captage.

    Source : SDAEP 2015 + collecte terrain.
    Utilité : Suivi de l'exploitation, détection de sous-exploitation ou surexploitation.
    """

    SOURCE_DONNEES_CHOICES = [
        ('SISPEA', 'SISPEA'),
        ('SDAEP_2015', 'SDAEP 2015'),
        ('COLLECTE_2025', 'Collecte terrain 2025'),
        ('ESTIME', 'Estimé'),
        ('CALCULE', 'Calculé'),
    ]

    captage = models.ForeignKey(
        'observatoire.Captage',
        on_delete=models.CASCADE,
        related_name='performances_annuelles',
        verbose_name="Captage"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    volume_preleve_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume prélevé (m³)"
    )
    volume_produit_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume produit (m³)"
    )

    debit_moyen_m3_h = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Débit moyen (m³/h)"
    )
    debit_pointe_m3_h = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Débit de pointe (m³/h)"
    )

    volume_pointe_mois_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume mois de pointe (m³)"
    )
    mois_pointe = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Mois de pointe",
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    volume_pointe_jour_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume jour de pointe (m³)"
    )

    nb_jours_exploitation = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de jours d'exploitation",
        help_text="Nombre de jours où le captage a été en service. Permet de détecter les captages utilisés en secours uniquement.",
        validators=[MinValueValidator(0), MaxValueValidator(366)]
    )
    nb_arrets = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre d'arrêts"
    )

    source_donnees = models.CharField(
        max_length=50,
        choices=SOURCE_DONNEES_CHOICES,
        blank=True,
        null=True,
        verbose_name="Source des données"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'captage_performances_annuelles'
        verbose_name = "Performance annuelle captage"
        verbose_name_plural = "Performances annuelles captages"
        unique_together = [['captage', 'annee']]
        ordering = ['-annee', 'captage__nom_captage']
        indexes = [
            models.Index(fields=['captage']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        return f"{self.captage.nom_captage} - {self.annee}"


class InterconnexionVolumeAnnuel(models.Model):
    """
    Volumes échangés annuellement via les interconnexions.

    Utilité : Calculer la dépendance d'une UGE aux achats d'eau.
    Exemple : UGE X achète 30% de son eau à UGE Y → dépendance à surveiller.
    """

    SOURCE_DONNEES_CHOICES = [
        ('SISPEA', 'SISPEA'),
        ('SDAEP_2015', 'SDAEP 2015'),
        ('COLLECTE_2025', 'Collecte terrain 2025'),
        ('ESTIME', 'Estimé'),
    ]

    interconnexion = models.ForeignKey(
        'observatoire.Interconnexion',
        on_delete=models.CASCADE,
        related_name='volumes_annuels',
        verbose_name="Interconnexion"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    volume_echange_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume échangé (m³)"
    )
    volume_pointe_mois_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume mois de pointe (m³)"
    )
    mois_pointe = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Mois de pointe",
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    prix_vente_euros_m3 = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Prix de vente (€/m³)"
    )
    cout_total_euros = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Coût total (€)"
    )

    source_donnees = models.CharField(
        max_length=50,
        choices=SOURCE_DONNEES_CHOICES,
        blank=True,
        null=True,
        verbose_name="Source des données"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'interconnexions_volumes_annuels'
        verbose_name = "Volume annuel interconnexion"
        verbose_name_plural = "Volumes annuels interconnexions"
        unique_together = [['interconnexion', 'annee']]
        ordering = ['-annee']
        indexes = [
            models.Index(fields=['interconnexion']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        return f"{self.interconnexion} - {self.annee}"


class CommuneDonneesAnnuelles(models.Model):
    """
    Données démographiques annuelles par commune.

    Sources : INSEE, fichiers communaux, SDAEP 2015.
    Utilité : Calculer les prévisions de besoins en eau (population × ratio consommation).
    """

    SOURCE_DONNEES_CHOICES = [
        ('INSEE', 'INSEE'),
        ('SDAEP_2015', 'SDAEP 2015'),
        ('COMMUNE', 'Fichiers communaux'),
        ('ESTIME', 'Estimé'),
    ]

    commune = models.ForeignKey(
        'observatoire.Commune',
        on_delete=models.CASCADE,
        related_name='donnees_annuelles',
        verbose_name="Commune"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    population_totale = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Population totale"
    )
    population_permanente = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Population permanente"
    )
    population_saisonniere = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Population saisonnière"
    )

    nb_logements_total = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de logements total"
    )
    nb_residences_principales = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de résidences principales"
    )
    nb_residences_secondaires = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de résidences secondaires"
    )
    nb_logements_vacants = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de logements vacants"
    )

    nb_logements_autorises = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de logements autorisés"
    )
    nb_logements_commences = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de logements commencés"
    )

    source_donnees = models.CharField(
        max_length=50,
        choices=SOURCE_DONNEES_CHOICES,
        blank=True,
        null=True,
        verbose_name="Source des données"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'communes_donnees_annuelles'
        verbose_name = "Données annuelles commune"
        verbose_name_plural = "Données annuelles communes"
        unique_together = [['commune', 'annee']]
        ordering = ['-annee', 'commune__nom']
        indexes = [
            models.Index(fields=['commune']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        return f"{self.commune.nom} - {self.annee}"


class CommuneTourismeAnnuel(models.Model):
    """
    Capacité d'accueil touristique par commune.

    Source : SDAEP 2015 + données offices de tourisme.
    Utilité : Calculer la population de pointe estivale (permanent + touristes).
    Formule : Pop. pointe = Pop. permanente + (Nb lits touristiques × Taux occupation).
    """

    SOURCE_DONNEES_CHOICES = [
        ('OFFICE_TOURISME', 'Office de tourisme'),
        ('SDAEP_2015', 'SDAEP 2015'),
        ('ESTIME', 'Estimé'),
    ]

    commune = models.ForeignKey(
        'observatoire.Commune',
        on_delete=models.CASCADE,
        related_name='tourisme_annuel',
        verbose_name="Commune"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    nb_lits_touristiques_total = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de lits touristiques total"
    )
    nb_lits_hotellerie = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de lits hôtellerie"
    )
    nb_lits_camping = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de lits camping"
    )
    nb_lits_locations_meublees = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de lits locations meublées"
    )
    nb_lits_residences_secondaires = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de lits résidences secondaires"
    )

    nb_nuitees_annuelles = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de nuitées annuelles"
    )
    nb_nuitees_mois_pointe = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de nuitées mois de pointe"
    )
    mois_pointe = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Mois de pointe",
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    population_equivalente_pointe = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Population équivalente de pointe"
    )

    source_donnees = models.CharField(
        max_length=50,
        choices=SOURCE_DONNEES_CHOICES,
        blank=True,
        null=True,
        verbose_name="Source des données"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = 'communes_tourisme_annuel'
        verbose_name = "Tourisme annuel commune"
        verbose_name_plural = "Tourisme annuel communes"
        unique_together = [['commune', 'annee']]
        ordering = ['-annee', 'commune__nom']
        indexes = [
            models.Index(fields=['commune']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        return f"{self.commune.nom} - {self.annee} (Tourisme)"


class UGEPatrimoineAnnuel(models.Model):
    """
    État du patrimoine réseau par UGE et par année.

    Source : SDAEP 2015 + collecte terrain.
    Utilité : Suivre le vieillissement du réseau, planifier les renouvellements.
    Indicateur clé : Taux de renouvellement = (Linéaire renouvelé / Linéaire total) × 100.
    """

    SOURCE_DONNEES_CHOICES = [
        ('SDAEP_2015', 'SDAEP 2015'),
        ('COLLECTE_2025', 'Collecte terrain 2025'),
        ('ESTIME', 'Estimé'),
    ]

    uge = models.ForeignKey(
        'observatoire.UGE',
        on_delete=models.CASCADE,
        related_name='patrimoine_annuel',
        verbose_name="UGE"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    lineaire_total_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire total (km)"
    )
    lineaire_fonte_grise_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire fonte grise (km)"
    )
    lineaire_fonte_ductile_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire fonte ductile (km)"
    )
    lineaire_amiante_ciment_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire amiante-ciment (km)"
    )
    lineaire_pvc_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire PVC (km)"
    )
    lineaire_pehd_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire PEHD (km)"
    )
    lineaire_autres_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire autres matériaux (km)"
    )

    lineaire_sup_50ans_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire > 50 ans (km)"
    )
    lineaire_sup_75ans_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire > 75 ans (km)"
    )
    age_moyen_reseau_ans = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Âge moyen du réseau (ans)"
    )

    nb_branchements_total = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de branchements total"
    )
    nb_branchements_plomb = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de branchements en plomb"
    )

    lineaire_renouvele_km = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Linéaire renouvelé (km)"
    )
    nb_branchements_renouveles = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de branchements renouvelés"
    )
    nb_branchements_plomb_renouveles = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de branchements plomb renouvelés"
    )

    nb_fuites_reparees = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de fuites réparées"
    )

    source_donnees = models.CharField(
        max_length=50,
        choices=SOURCE_DONNEES_CHOICES,
        blank=True,
        null=True,
        verbose_name="Source des données"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = 'uge_patrimoine_annuel'
        verbose_name = "Patrimoine annuel UGE"
        verbose_name_plural = "Patrimoine annuel UGE"
        unique_together = [['uge', 'annee']]
        ordering = ['-annee', 'uge__nom_uge']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        return f"{self.uge.nom_uge} - {self.annee} (Patrimoine)"
