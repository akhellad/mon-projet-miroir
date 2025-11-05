"""
Modèles de bilans et plans d'action pour l'Observatoire SDAEP.

SECTION 6 : BILANS ET PLANS D'ACTION

Ces modèles gèrent les bilans de vulnérabilité et les actions à mener.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class BilanBesoinsRessources(models.Model):
    """
    Bilan besoins/ressources par UGE (satisfaction des besoins).

    Source : Calcul à partir des données collectées.
    Utilité : Identifier les UGE en situation de tension ou d'excédent.
    Formule : Taux satisfaction = (Ressources disponibles / Besoins) × 100.
    """

    STATUT_BILAN_CHOICES = [
        ('EXCEDENT', 'Excédent (> 120%)'),
        ('EQUILIBRE', 'Équilibre (100-120%)'),
        ('TENSION', 'Tension (80-100%)'),
        ('DEFICIT', 'Déficit (< 80%)'),
    ]

    uge = models.ForeignKey(
        'observatoire.UGE',
        on_delete=models.CASCADE,
        related_name='bilans_besoins_ressources',
        verbose_name="UGE"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année de référence",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    # Besoins (en m³/j)
    besoin_moyen_jour_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Besoin moyen journalier (m³/j)"
    )
    besoin_pointe_jour_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Besoin jour de pointe (m³/j)"
    )
    besoin_moyen_mois_ete_m3_j = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Besoin moyen mois d'été (m³/j)"
    )

    # Ressources disponibles (en m³/j)
    ressource_totale_dispo_m3_j = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Ressource totale disponible (m³/j)",
        help_text="Somme des débits max des captages + achats d'eau"
    )
    ressource_propre_m3_j = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Ressource propre (m³/j)",
        help_text="Uniquement les captages (sans achats)"
    )
    ressource_achetee_m3_j = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Ressource achetée (m³/j)"
    )
    ressource_secours_m3_j = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Ressource de secours (m³/j)",
        help_text="Captages de secours, utilisés uniquement en période de crise"
    )

    # Indicateurs calculés
    taux_satisfaction_moyen = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de satisfaction moyen (%)",
        help_text="= (Ressource dispo / Besoin moyen) × 100",
        validators=[MinValueValidator(Decimal('0'))]
    )
    taux_satisfaction_pointe = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de satisfaction en pointe (%)",
        help_text="= (Ressource dispo / Besoin pointe) × 100",
        validators=[MinValueValidator(Decimal('0'))]
    )
    taux_autonomie = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux d'autonomie (%)",
        help_text="= (Ressource propre / Besoin moyen) × 100. Indique la dépendance aux achats d'eau.",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    statut_bilan = models.CharField(
        max_length=20,
        choices=STATUT_BILAN_CHOICES,
        blank=True,
        null=True,
        verbose_name="Statut du bilan"
    )

    # Capacité de stockage
    volume_stockage_total_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume de stockage total (m³)"
    )
    autonomie_stockage_jours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Autonomie de stockage (jours)",
        help_text="= Volume stockage / Besoin moyen journalier"
    )

    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires et analyse"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'bilans_besoins_ressources'
        verbose_name = "Bilan besoins/ressources"
        verbose_name_plural = "Bilans besoins/ressources"
        unique_together = [['uge', 'annee']]
        ordering = ['-annee', 'uge__nom_uge']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['annee']),
            models.Index(fields=['statut_bilan']),
        ]

    def __str__(self):
        return f"{self.uge.nom_uge} - Bilan {self.annee}"


class VulnerabiliteUGE(models.Model):
    """
    Évaluation de la vulnérabilité par UGE.

    Source : SDAEP Phase 1 + analyse terrain.
    Utilité : Prioriser les actions, identifier les zones à risque.
    Méthode : Score multicritère (ressource, qualité, patrimoine, gestion).
    """

    NIVEAU_VULNERABILITE_CHOICES = [
        ('FAIBLE', 'Faible'),
        ('MOYEN', 'Moyen'),
        ('ELEVE', 'Élevé'),
        ('TRES_ELEVE', 'Très élevé'),
    ]

    uge = models.ForeignKey(
        'observatoire.UGE',
        on_delete=models.CASCADE,
        related_name='vulnerabilites',
        verbose_name="UGE"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année d'évaluation",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    # Scores par thématique (1-5 : 1=Très faible, 5=Très élevée)
    score_ressource = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Score vulnérabilité ressource",
        help_text="Basé sur : suffisance quantitative, diversification des sources, dépendance aux achats",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    score_qualite = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Score vulnérabilité qualité",
        help_text="Basé sur : conformité réglementaire, existence de périmètres de protection, pollutions identifiées",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    score_patrimoine = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Score vulnérabilité patrimoine",
        help_text="Basé sur : rendement réseau, âge des ouvrages, taux de renouvellement",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    score_gestion = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Score vulnérabilité gestion",
        help_text="Basé sur : exploitation (régie/DSP), télégestion, connaissance patrimoine",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    score_global = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name="Score global de vulnérabilité",
        help_text="Moyenne pondérée des 4 scores thématiques",
        validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('5.0'))]
    )
    niveau_vulnerabilite = models.CharField(
        max_length=20,
        choices=NIVEAU_VULNERABILITE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Niveau de vulnérabilité"
    )

    # Points faibles identifiés
    ressource_insuffisante = models.BooleanField(
        default=False,
        verbose_name="Ressource insuffisante"
    )
    qualite_degradee = models.BooleanField(
        default=False,
        verbose_name="Qualité dégradée"
    )
    reseau_vetuste = models.BooleanField(
        default=False,
        verbose_name="Réseau vétuste"
    )
    forte_dependance_achats = models.BooleanField(
        default=False,
        verbose_name="Forte dépendance aux achats"
    )
    captages_vulnerables = models.BooleanField(
        default=False,
        verbose_name="Captages vulnérables"
    )

    recommandations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Recommandations"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'vulnerabilites_uge'
        verbose_name = "Vulnérabilité UGE"
        verbose_name_plural = "Vulnérabilités UGE"
        unique_together = [['uge', 'annee']]
        ordering = ['-annee', 'uge__nom_uge']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['annee']),
            models.Index(fields=['niveau_vulnerabilite']),
        ]

    def __str__(self):
        return f"{self.uge.nom_uge} - Vulnérabilité {self.annee}"


class PlanAction(models.Model):
    """
    Plan d'actions pour améliorer la sécurisation de l'AEP.

    Source : Concertation SDAEP.
    Utilité : Suivi des projets d'amélioration, planification des investissements.
    Granularité : 1 ligne = 1 action pour 1 UGE (ou 1 commune).
    """

    TYPE_ACTION_CHOICES = [
        ('RESSOURCE', 'Sécurisation de la ressource'),
        ('INTERCONNEXION', 'Création/renforcement interconnexion'),
        ('RESEAU', 'Renouvellement/extension réseau'),
        ('OUVRAGE', 'Création/rénovation ouvrage'),
        ('PROTECTION', 'Protection captage (DUP)'),
        ('TRAITEMENT', 'Amélioration traitement'),
        ('GESTION', 'Amélioration gestion'),
        ('AUTRE', 'Autre'),
    ]

    PRIORITE_CHOICES = [
        ('TRES_HAUTE', 'Très haute'),
        ('HAUTE', 'Haute'),
        ('MOYENNE', 'Moyenne'),
        ('FAIBLE', 'Faible'),
    ]

    STATUT_ACTION_CHOICES = [
        ('ENVISAGEE', 'Envisagée'),
        ('PROGRAMMEE', 'Programmée'),
        ('EN_COURS', 'En cours'),
        ('REALISEE', 'Réalisée'),
        ('ABANDONNEE', 'Abandonnée'),
    ]

    code_action = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code action",
        help_text="Identifiant unique de l'action"
    )
    nom_action = models.CharField(
        max_length=300,
        verbose_name="Nom de l'action"
    )

    uge = models.ForeignKey(
        'observatoire.UGE',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plans_actions',
        verbose_name="UGE"
    )
    commune = models.ForeignKey(
        'observatoire.Commune',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plans_actions',
        verbose_name="Commune"
    )

    type_action = models.CharField(
        max_length=30,
        choices=TYPE_ACTION_CHOICES,
        verbose_name="Type d'action"
    )
    priorite = models.CharField(
        max_length=20,
        choices=PRIORITE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Priorité"
    )
    statut_action = models.CharField(
        max_length=20,
        choices=STATUT_ACTION_CHOICES,
        default='ENVISAGEE',
        verbose_name="Statut de l'action"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description détaillée"
    )
    objectif = models.TextField(
        blank=True,
        null=True,
        verbose_name="Objectif visé"
    )

    # Planification
    annee_debut_prevue = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Année de début prévue",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    annee_fin_prevue = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Année de fin prévue",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    annee_realisation = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Année de réalisation effective",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    # Coûts
    cout_estime_euros = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Coût estimé (€)"
    )
    cout_reel_euros = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Coût réel (€)"
    )

    # Financement
    taux_subvention = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de subvention (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    financeurs = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name="Financeurs",
        help_text="Agence de l'eau, Département, Région, Europe..."
    )

    maitre_ouvrage = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Maître d'ouvrage"
    )
    maitre_oeuvre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Maître d'œuvre"
    )

    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires et suivi"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'plans_actions'
        verbose_name = "Plan d'action"
        verbose_name_plural = "Plans d'actions"
        ordering = ['priorite', '-annee_debut_prevue', 'nom_action']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['commune']),
            models.Index(fields=['type_action']),
            models.Index(fields=['priorite']),
            models.Index(fields=['statut_action']),
            models.Index(fields=['annee_debut_prevue']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.annee_debut_prevue and self.annee_fin_prevue and
            self.annee_debut_prevue > self.annee_fin_prevue):
            raise ValidationError({
                'annee_fin_prevue': 'L\'année de fin doit être postérieure à l\'année de début.'
            })

    def __str__(self):
        return f"{self.code_action} - {self.nom_action}"
