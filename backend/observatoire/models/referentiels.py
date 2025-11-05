"""
Modèles de référentiels et métadonnées pour l'Observatoire SDAEP.

SECTION 8 : RÉFÉRENTIELS ET MÉTADONNÉES

Ces modèles gèrent les données de référence et les métadonnées système.
"""

from django.db import models
from django.conf import settings


class SourceDonnees(models.Model):
    """
    Référentiel des sources de données.

    Utilité : Traçabilité des données, gestion des imports.
    Exemples : SISPEA 2023, SDAEP 2015, Collecte terrain 2025, INSEE 2024.
    """

    TYPE_SOURCE_CHOICES = [
        ('OFFICIELLE', 'Source officielle'),
        ('COLLECTE', 'Collecte terrain'),
        ('ESTIMATION', 'Estimation'),
        ('CALCUL', 'Calcul automatique'),
    ]

    code_source = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code source",
        help_text="Identifiant court : SISPEA_2023, SDAEP_2015, INSEE_2024"
    )
    nom_source = models.CharField(
        max_length=200,
        verbose_name="Nom de la source"
    )

    type_source = models.CharField(
        max_length=20,
        choices=TYPE_SOURCE_CHOICES,
        verbose_name="Type de source"
    )

    organisme = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Organisme producteur",
        help_text="Ex : SISPEA, INSEE, ARS, DDT07"
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL d'accès"
    )

    date_reference = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de référence des données"
    )
    date_collecte = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de collecte"
    )
    date_import = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'import dans la BDD"
    )

    fiabilite = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Fiabilité estimée",
        help_text="Haute, Moyenne, Faible"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    notes_methodologie = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes de méthodologie"
    )

    actif = models.BooleanField(
        default=True,
        verbose_name="Source active"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = 'sources_donnees'
        verbose_name = "Source de données"
        verbose_name_plural = "Sources de données"
        ordering = ['-date_reference', 'nom_source']
        indexes = [
            models.Index(fields=['code_source']),
            models.Index(fields=['type_source']),
        ]

    def __str__(self):
        return f"{self.nom_source} ({self.code_source})"


class ImportHistorique(models.Model):
    """
    Historique des imports de données.

    Utilité : Traçabilité, débogage, gestion des versions.
    Permet de savoir quand et comment chaque jeu de données a été importé.
    """

    STATUT_IMPORT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('REUSSI', 'Réussi'),
        ('ERREUR', 'Erreur'),
        ('PARTIEL', 'Partiel'),
    ]

    TYPE_IMPORT_CHOICES = [
        ('INITIAL', 'Import initial'),
        ('MAJ', 'Mise à jour'),
        ('CORRECTION', 'Correction'),
    ]

    source = models.ForeignKey(
        SourceDonnees,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imports',
        verbose_name="Source de données"
    )

    date_import = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date et heure de l'import"
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imports_realises',
        verbose_name="Utilisateur"
    )

    type_import = models.CharField(
        max_length=20,
        choices=TYPE_IMPORT_CHOICES,
        verbose_name="Type d'import"
    )
    statut_import = models.CharField(
        max_length=20,
        choices=STATUT_IMPORT_CHOICES,
        default='EN_COURS',
        verbose_name="Statut de l'import"
    )

    table_cible = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Table cible",
        help_text="Nom de la table importée"
    )
    fichier_source = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Fichier source"
    )

    nb_lignes_importees = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de lignes importées"
    )
    nb_lignes_erreur = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de lignes en erreur"
    )
    nb_lignes_total = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de lignes total"
    )

    duree_secondes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Durée (secondes)"
    )

    log_import = models.TextField(
        blank=True,
        null=True,
        verbose_name="Log de l'import",
        help_text="Messages d'erreur et avertissements"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    class Meta:
        db_table = 'imports_historique'
        verbose_name = "Import historique"
        verbose_name_plural = "Imports historiques"
        ordering = ['-date_import']
        indexes = [
            models.Index(fields=['source']),
            models.Index(fields=['date_import']),
            models.Index(fields=['statut_import']),
            models.Index(fields=['table_cible']),
        ]

    def __str__(self):
        return f"Import {self.table_cible} - {self.date_import.strftime('%Y-%m-%d %H:%M')}"


class Glossaire(models.Model):
    """
    Glossaire des termes techniques.

    Utilité : Aide contextuelle dans l'interface, documentation.
    Exemple : "UGE", "DUP", "Rendement réseau", "SISPEA".
    """

    CATEGORIE_CHOICES = [
        ('SIGLE', 'Sigle'),
        ('INDICATEUR', 'Indicateur'),
        ('OUVRAGE', 'Type d\'ouvrage'),
        ('REGLEMENTAIRE', 'Terme réglementaire'),
        ('TECHNIQUE', 'Terme technique'),
    ]

    terme = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Terme"
    )
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Catégorie"
    )

    definition = models.TextField(
        verbose_name="Définition"
    )
    exemple = models.TextField(
        blank=True,
        null=True,
        verbose_name="Exemple d'utilisation"
    )

    synonymes = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Synonymes",
        help_text="Séparés par des virgules"
    )
    reference_reglementaire = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Référence réglementaire",
        help_text="Ex : Code de la santé publique article R1321-1"
    )

    ordre_affichage = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Ordre d'affichage"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'glossaire'
        verbose_name = "Terme du glossaire"
        verbose_name_plural = "Glossaire"
        ordering = ['terme']
        indexes = [
            models.Index(fields=['terme']),
            models.Index(fields=['categorie']),
        ]

    def __str__(self):
        return self.terme


class Configuration(models.Model):
    """
    Configuration et paramètres de l'observatoire.

    Utilité : Paramétrage global de l'application.
    Exemples : Année de référence, seuils d'alerte, contacts, logos.
    """

    TYPE_VALEUR_CHOICES = [
        ('STRING', 'Texte'),
        ('INTEGER', 'Nombre entier'),
        ('DECIMAL', 'Nombre décimal'),
        ('BOOLEAN', 'Booléen'),
        ('DATE', 'Date'),
        ('JSON', 'JSON'),
    ]

    cle = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Clé de configuration",
        help_text="Ex : annee_reference, seuil_rendement_critique, email_contact"
    )
    valeur = models.TextField(
        verbose_name="Valeur"
    )
    type_valeur = models.CharField(
        max_length=20,
        choices=TYPE_VALEUR_CHOICES,
        default='STRING',
        verbose_name="Type de valeur"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    categorie = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Catégorie",
        help_text="Ex : General, Alertes, Contact, Affichage"
    )

    modifiable_interface = models.BooleanField(
        default=True,
        verbose_name="Modifiable via l'interface"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'configuration'
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"
        ordering = ['categorie', 'cle']
        indexes = [
            models.Index(fields=['cle']),
            models.Index(fields=['categorie']),
        ]

    def __str__(self):
        return f"{self.cle} = {self.valeur}"
