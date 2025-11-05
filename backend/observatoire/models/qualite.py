"""
Modèles de qualité de l'eau pour l'Observatoire SDAEP.

SECTION 5 : QUALITÉ DE L'EAU

Ces modèles gèrent les analyses de qualité de l'eau, les paramètres mesurés
et la conformité réglementaire.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class ParametreQualite(models.Model):
    """
    Référentiel des paramètres de qualité de l'eau.

    Source : Code de la santé publique + base SANDRE.
    Familles : Microbiologique, Physico-chimique, Pesticides, Métaux lourds.
    Utilité : Référence pour les analyses et le calcul de conformité.
    """

    FAMILLE_PARAMETRE_CHOICES = [
        ('MICRO', 'Microbiologique'),
        ('PHYSI', 'Physico-chimique'),
        ('PESTI', 'Pesticides'),
        ('METAL', 'Métaux lourds'),
        ('ORGA', 'Matières organiques'),
    ]

    code_sise_eau = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code SISE-EAUX"
    )
    code_sandre = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Code SANDRE"
    )

    nom_parametre = models.CharField(
        max_length=200,
        verbose_name="Nom du paramètre"
    )
    nom_court = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Nom court"
    )
    unite = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Unité"
    )

    famille_parametre = models.CharField(
        max_length=50,
        choices=FAMILLE_PARAMETRE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Famille de paramètre"
    )

    limite_qualite_max = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Limite de qualité max",
        help_text="Limite de qualité réglementaire (ne doit pas être dépassée). Ex : Turbidité ≤ 1 NFU, Nitrates ≤ 50 mg/L."
    )
    limite_qualite_min = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Limite de qualité min"
    )
    limite_reference_max = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Limite de référence max",
        help_text="Référence de qualité (recommandation, non obligatoire). Ex : Dureté recommandée entre 15 et 25 °F."
    )
    limite_reference_min = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Limite de référence min"
    )

    parametre_sante = models.BooleanField(
        default=False,
        verbose_name="Paramètre de santé",
        help_text="Vrai si paramètre lié à la santé publique"
    )
    parametre_indicateur = models.BooleanField(
        default=False,
        verbose_name="Paramètre indicateur",
        help_text="Vrai si paramètre indicateur (non sanitaire)"
    )

    ordre_affichage = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Ordre d'affichage"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = 'parametres_qualite'
        verbose_name = "Paramètre de qualité"
        verbose_name_plural = "Paramètres de qualité"
        ordering = ['ordre_affichage', 'nom_parametre']
        indexes = [
            models.Index(fields=['code_sise_eau']),
            models.Index(fields=['famille_parametre']),
            models.Index(fields=['parametre_sante']),
        ]

    def __str__(self):
        return f"{self.nom_court or self.nom_parametre} ({self.code_sise_eau})"


class AnalyseQualite(models.Model):
    """
    TABLE GÉNÉRIQUE : Toutes les analyses de qualité de l'eau.

    Remplace 15+ tables dispersées de l'ancien schéma (udi_qualite_*, captage_param_non_conf, etc.).
    Granularité : 1 ligne = 1 ouvrage × 1 paramètre × 1 année (données agrégées).
    Type d'ouvrage : captage, udi, station_traitement, reservoir, reseau.
    Source : ARS/SISE-EAUX (analyses réglementaires) + auto-contrôles exploitant.
    """

    TYPE_OUVRAGE_CHOICES = [
        ('captage', 'Captage'),
        ('udi', 'UDI'),
        ('melange_captage', 'Mélange de captages'),
        ('station_traitement', 'Station de traitement'),
        ('reservoir', 'Réservoir'),
        ('reseau', 'Réseau'),
    ]

    TYPE_PRELEVEMENT_CHOICES = [
        ('REGLEMENTAIRE', 'Réglementaire (ARS)'),
        ('AUTO_CONTROLE', 'Auto-contrôle (exploitant)'),
        ('SURVEILLANCE', 'Surveillance (contrôle sanitaire)'),
    ]

    CLASSE_QUALITE_CHOICES = [
        ('A', 'A - Excellent'),
        ('B', 'B - Bon'),
        ('C', 'C - Passable'),
        ('D', 'D - Médiocre'),
        ('E', 'E - Mauvais'),
    ]

    SOURCE_DONNEES_CHOICES = [
        ('ARS', 'ARS/SISE-EAUX'),
        ('EXPLOITANT', 'Exploitant'),
        ('LABORATOIRE', 'Laboratoire'),
    ]

    annee = models.PositiveSmallIntegerField(
        verbose_name="Année",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    type_ouvrage = models.CharField(
        max_length=20,
        choices=TYPE_OUVRAGE_CHOICES,
        verbose_name="Type d'ouvrage"
    )
    ouvrage_id = models.BigIntegerField(
        verbose_name="ID de l'ouvrage",
        help_text="ID de l'ouvrage concerné (captage_id, udi_id, etc.)"
    )

    parametre = models.ForeignKey(
        ParametreQualite,
        on_delete=models.RESTRICT,
        related_name='analyses',
        verbose_name="Paramètre"
    )

    type_prelevement = models.CharField(
        max_length=50,
        choices=TYPE_PRELEVEMENT_CHOICES,
        blank=True,
        null=True,
        verbose_name="Type de prélèvement",
        help_text='Type : "Réglementaire" (ARS), "Auto-contrôle" (exploitant), "Surveillance" (contrôle sanitaire).'
    )
    nb_prelevements = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de prélèvements"
    )
    nb_non_conformes = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de non-conformes"
    )

    valeur_moyenne = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Valeur moyenne"
    )
    valeur_max = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Valeur maximale"
    )
    valeur_min = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Valeur minimale"
    )
    valeur_mediane = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Valeur médiane"
    )
    valeur_percentile_95 = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Valeur percentile 95"
    )

    taux_conformite = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de conformité (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    classe_qualite = models.CharField(
        max_length=5,
        choices=CLASSE_QUALITE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Classe de qualité",
        help_text='Classe : A (Excellent), B (Bon), C (Passable), D (Médiocre), E (Mauvais). Calculée automatiquement selon grilles ARS.'
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
        db_table = 'analyses_qualite'
        verbose_name = "Analyse de qualité"
        verbose_name_plural = "Analyses de qualité"
        ordering = ['-annee', 'type_ouvrage', 'ouvrage_id']
        indexes = [
            models.Index(fields=['annee']),
            models.Index(fields=['type_ouvrage', 'ouvrage_id']),
            models.Index(fields=['parametre']),
            models.Index(fields=['annee', 'type_ouvrage', 'ouvrage_id']),
        ]

    def __str__(self):
        return f"{self.type_ouvrage} #{self.ouvrage_id} - {self.parametre.nom_court} - {self.annee}"


class UGEConformiteAnnuelle(models.Model):
    """
    Synthèse de conformité réglementaire par UGE.

    Source : Calcul à partir de analyses_qualite + données ARS.
    Utilité : Indicateur de conformité pour les tableaux de bord.
    Règle : UGE conforme si taux_conformite_bacterio ≥ 95% ET taux_conformite_physico ≥ 95%.
    """

    SOURCE_DONNEES_CHOICES = [
        ('ARS', 'ARS/SISE-EAUX'),
        ('CALCULE', 'Calculé'),
    ]

    uge = models.ForeignKey(
        'observatoire.UGE',
        on_delete=models.CASCADE,
        related_name='conformites_annuelles',
        verbose_name="UGE"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    nb_prelevements_bacterio = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de prélèvements bactériologiques"
    )
    nb_non_conformes_bacterio = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de non-conformes bactériologiques"
    )
    taux_conformite_bacterio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de conformité bactériologique (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    nb_prelevements_physico = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de prélèvements physico-chimiques"
    )
    nb_non_conformes_physico = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de non-conformes physico-chimiques"
    )
    taux_conformite_physico = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de conformité physico-chimique (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    taux_conformite_global = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux de conformité global (%)",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    conforme_reglementaire = models.BooleanField(
        default=False,
        verbose_name="Conforme réglementaire",
        help_text="Vrai si taux_conformite_bacterio ≥ 95% ET taux_conformite_physico ≥ 95%"
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
        db_table = 'uge_conformite_annuelle'
        verbose_name = "Conformité annuelle UGE"
        verbose_name_plural = "Conformités annuelles UGE"
        unique_together = [['uge', 'annee']]
        ordering = ['-annee', 'uge__nom_uge']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        return f"{self.uge.nom_uge} - {self.annee} (Conformité)"
