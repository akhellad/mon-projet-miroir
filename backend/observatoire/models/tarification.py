"""
Modèles de tarification pour l'Observatoire SDAEP.

SECTION 7 : TARIFICATION

Ces modèles gèrent les grilles tarifaires et l'évolution des prix de l'eau.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class GrilleTarifaire(models.Model):
    """
    Grille tarifaire par UGE et par année.

    Source : SISPEA + collecte terrain.
    Utilité : Comparaison des prix, suivi de l'évolution tarifaire.
    Modèle : Part fixe (abonnement annuel) + Part variable (€/m³).
    """

    TYPE_TARIF_CHOICES = [
        ('SIMPLIFIE', 'Simplifié (1 tranche)'),
        ('PROGRESSIF', 'Progressif (tranches)'),
        ('DEGRESSIF', 'Dégressif'),
    ]

    uge = models.ForeignKey(
        'observatoire.UGE',
        on_delete=models.CASCADE,
        related_name='grilles_tarifaires',
        verbose_name="UGE"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année d'application"
    )

    type_tarif = models.CharField(
        max_length=20,
        choices=TYPE_TARIF_CHOICES,
        default='SIMPLIFIE',
        verbose_name="Type de tarif"
    )

    # Part fixe (abonnement annuel)
    part_fixe_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Part fixe HT (€/an)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    part_fixe_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Part fixe TTC (€/an)",
        validators=[MinValueValidator(Decimal('0'))]
    )

    # Part variable (pour la 1ère tranche ou tarif unique)
    prix_m3_ht = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Prix au m³ HT (€/m³)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    prix_m3_ttc = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Prix au m³ TTC (€/m³)",
        validators=[MinValueValidator(Decimal('0'))]
    )

    # Prix total pour 120 m³/an (référence nationale)
    prix_120m3_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Prix pour 120 m³ HT (€)",
        help_text="Prix de référence national : consommation type d'un foyer",
        validators=[MinValueValidator(Decimal('0'))]
    )
    prix_120m3_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Prix pour 120 m³ TTC (€)",
        validators=[MinValueValidator(Decimal('0'))]
    )

    # Taxes et redevances
    redevance_agence_eau_m3 = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Redevance Agence de l'eau (€/m³)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    redevance_vne_m3 = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Redevance Voies Navigables (€/m³)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    tva_taux = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.5'),
        verbose_name="Taux de TVA (%)",
        help_text="TVA réduite : 5,5% pour l'eau potable"
    )

    # Date d'application
    date_application = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'application"
    )
    date_fin_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin de validité"
    )

    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'grilles_tarifaires'
        verbose_name = "Grille tarifaire"
        verbose_name_plural = "Grilles tarifaires"
        unique_together = [['uge', 'annee']]
        ordering = ['-annee', 'uge__nom_uge']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        return f"{self.uge.nom_uge} - Tarif {self.annee}"


class TrancheTarifaire(models.Model):
    """
    Tranches tarifaires pour les tarifs progressifs.

    Utilité : Gérer les tarifs progressifs (prix différent par tranche de consommation).
    Exemple : 0-50 m³ : 1,50€/m³, 51-120 m³ : 2,00€/m³, >120 m³ : 2,50€/m³.
    """

    grille = models.ForeignKey(
        GrilleTarifaire,
        on_delete=models.CASCADE,
        related_name='tranches',
        verbose_name="Grille tarifaire"
    )

    numero_tranche = models.PositiveSmallIntegerField(
        verbose_name="Numéro de tranche",
        help_text="1, 2, 3, etc."
    )
    volume_min_m3 = models.PositiveIntegerField(
        verbose_name="Volume minimum (m³)",
        help_text="Début de la tranche (inclus)"
    )
    volume_max_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume maximum (m³)",
        help_text="Fin de la tranche (inclus). NULL = illimité"
    )

    prix_m3_ht = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        verbose_name="Prix au m³ HT (€/m³)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    prix_m3_ttc = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        verbose_name="Prix au m³ TTC (€/m³)",
        validators=[MinValueValidator(Decimal('0'))]
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = 'tranches_tarifaires'
        verbose_name = "Tranche tarifaire"
        verbose_name_plural = "Tranches tarifaires"
        unique_together = [['grille', 'numero_tranche']]
        ordering = ['grille', 'numero_tranche']
        indexes = [
            models.Index(fields=['grille']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.volume_max_m3 and self.volume_min_m3 >= self.volume_max_m3):
            raise ValidationError({
                'volume_max_m3': 'Le volume maximum doit être supérieur au volume minimum.'
            })

    def __str__(self):
        if self.volume_max_m3:
            return f"Tranche {self.numero_tranche} : {self.volume_min_m3}-{self.volume_max_m3} m³"
        return f"Tranche {self.numero_tranche} : ≥ {self.volume_min_m3} m³"
