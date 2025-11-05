"""
Modèles de données pour l'Observatoire SDAEP.

Définit la structure de stockage des couches géographiques et de leurs entités
dans PostgreSQL/PostGIS.
"""

from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class Layer(models.Model):
    """
    Modèle représentant une couche géographique (layer SIG).

    Une couche regroupe des entités de même nature (communes, captages, conduites, etc.)
    avec des métadonnées de style et de configuration pour l'affichage cartographique.
    """
    GEOMETRY_TYPES = [
        ('Point', 'Point'),
        ('LineString', 'Ligne'),
        ('Polygon', 'Polygone'),
        ('MultiPoint', 'Multi-points'),
        ('MultiLineString', 'Multi-lignes'),
        ('MultiPolygon', 'Multi-polygones'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom de la couche")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    geometry_type = models.CharField(max_length=50, choices=GEOMETRY_TYPES, verbose_name="Type de géométrie")
    identifier_field = models.CharField(max_length=100, default='id', verbose_name="Champ identifiant")

    # Configuration de style pour l'affichage cartographique
    style_color = models.CharField(max_length=7, default='#3388ff', verbose_name="Couleur")
    style_weight = models.IntegerField(default=2, verbose_name="Épaisseur du trait")
    style_opacity = models.FloatField(default=0.8, verbose_name="Opacité")
    style_fill_opacity = models.FloatField(default=0.2, verbose_name="Opacité du remplissage")

    # Métadonnées de source et référencement spatial
    source_file = models.CharField(max_length=500, blank=True, null=True, verbose_name="Fichier source")
    srid = models.IntegerField(default=2154, verbose_name="SRID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    # Contrôle de visibilité
    visible = models.BooleanField(default=True, verbose_name="Visible par défaut")

    # Ordre d'affichage (z-index) sur la carte
    order = models.IntegerField(default=0, verbose_name="Ordre d'affichage", help_text="Plus la valeur est élevée, plus la couche est au-dessus")

    class Meta:
        db_table = 'layers'
        ordering = ['-order', 'name']

    def __str__(self):
        return self.name


class Feature(models.Model):
    """
    Modèle représentant une entité géographique.

    Chaque feature appartient à une couche et contient une géométrie PostGIS
    ainsi que des propriétés alphanumériques stockées en JSON pour une flexibilité maximale.
    """
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name='features', verbose_name="Couche")

    # Géométrie PostGIS (type générique supportant tous les types de géométries)
    geom = models.GeometryField(srid=2154, verbose_name="Géométrie")

    # Métadonnées de suivi
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'features'
        indexes = [
            models.Index(fields=['layer']),
        ]

    def __str__(self):
        return f"Feature #{self.pk} - {self.layer.name}"

class Arrondissement(models.Model):
    """
    Modèle représentant les arrondissements du département de l'Ardèche.
    
    Découpage administratif territorial de niveau supérieur aux communes.
    """
    
    code_arrondissement = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="Code d'arrondissement",
        help_text="Code INSEE de l'arrondissement"
    )
    nom_arrondissement = models.CharField(
        max_length=200, 
        verbose_name="Nom de l'arrondissement",
        db_index=True
    )
    
    # Géométrie
    feature = models.OneToOneField(
        Feature,
        on_delete=models.CASCADE,
        related_name='arrondissement',
        verbose_name="Entité géographique associée"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'arrondissements'
        ordering = ['nom_arrondissement']
        verbose_name = "Arrondissement"
        verbose_name_plural = "Arrondissements"
        indexes = [
            models.Index(fields=['code_arrondissement']),
            models.Index(fields=['nom_arrondissement']),
        ]
    
    def __str__(self):
        return f"{self.nom_arrondissement} ({self.code_arrondissement})"

class Canton(models.Model):
    """
    Modèle représentant les cantons du département de l'Ardèche.
    
    Découpage administratif territorial de niveau intermédiaire.
    """
    
    code_canton = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="Code de canton",
        help_text="Code INSEE du canton"
    )
    nom_canton = models.CharField(
        max_length=200, 
        verbose_name="Nom du canton",
        db_index=True
    )
    
    # Relation avec l'arrondissement
    arrondissement = models.ForeignKey(
        Arrondissement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cantons',
        verbose_name="Arrondissement"
    )
    
    # Géométrie
    feature = models.OneToOneField(
        Feature,
        on_delete=models.CASCADE,
        related_name='canton',
        verbose_name="Entité géographique associée"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'cantons'
        ordering = ['nom_canton']
        verbose_name = "Canton"
        verbose_name_plural = "Cantons"
        indexes = [
            models.Index(fields=['code_canton']),
            models.Index(fields=['nom_canton']),
            models.Index(fields=['arrondissement']),
        ]
    
    def __str__(self):
        return f"{self.nom_canton} ({self.code_canton})"
    
class Commune(models.Model):
    """
    Modèle représentant les communes du département de l'Ardèche.
    
    Contient les informations administratives et géographiques des communes,
    avec une géométrie stockée directement dans le modèle.
    """
    
    # Types de documents d'urbanisme
    TYPE_DOC_URBA_CHOICES = [
        ('PLU', 'Plan Local d\'Urbanisme'),
        ('POS', 'Plan d\'Occupation des Sols'),
        ('CC', 'Carte Communale'),
        ('RNU', 'Règlement National d\'Urbanisme'),
        ('AUCUN', 'Aucun document'),
    ]
    
    # Champs principaux
    code_insee = models.CharField(
        max_length=5, 
        unique=True, 
        verbose_name="Code INSEE",
        help_text="Code INSEE à 5 chiffres de la commune"
    )
    nom = models.CharField(
        max_length=200, 
        verbose_name="Nom de la commune",
        db_index=True
    )
    
    # Relations territoriales
    arrondissement = models.ForeignKey(
        'Arrondissement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='communes',
        verbose_name="Arrondissement"
    )
    canton = models.ForeignKey(
        'Canton',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='communes',
        verbose_name="Canton"
    )
    zone_emploi = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Zone d'emploi"
    )
    
    # Urbanisme
    type_doc_urba_approuve = models.CharField(
        max_length=10,
        choices=TYPE_DOC_URBA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Type de document d'urbanisme approuvé"
    )
    document_urbanisme = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Document d'urbanisme",
        help_text="Type de document : PLU, PLUi, Carte communale, RNU (Règlement National d'Urbanisme)"
    )
    date_doc_urba_approuve = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date du document d'urbanisme approuvé"
    )
    date_approbation_urba = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'approbation urbanisme"
    )
    type_doc_urba_en_cours = models.CharField(
        max_length=10,
        choices=TYPE_DOC_URBA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Type de document d'urbanisme en cours"
    )
    commentaires_generaux_urba_previs = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires généraux urbanisme prévisionnel"
    )
    
    # Caractéristiques géographiques
    superficie_km2 = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Superficie (km²)",
        validators=[MinValueValidator(Decimal('0.001'))]
    )

    # Données démographiques
    population = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Population",
        help_text="Population municipale"
    )
    population_projection_2030 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Projection population 2030",
        help_text="Projection démographique issue du PLU ou INSEE"
    )
    population_projection_2040 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Projection population 2040",
        help_text="Projection démographique issue du PLU ou INSEE"
    )

    # Informations mairie
    nom_mairie = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Nom de la mairie"
    )
    adresse_mairie = models.CharField(
        max_length=300, 
        blank=True, 
        null=True, 
        verbose_name="Adresse de la mairie"
    )
    code_postal_commune = models.CharField(
        max_length=10, 
        blank=True, 
        null=True, 
        verbose_name="Code postal de la commune"
    )
    telephone_mairie = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Téléphone de la mairie"
    )
    fax_mairie = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Fax de la mairie"
    )
    email_mairie = models.EmailField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Email de la mairie"
    )
    mobile_mairie = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Mobile de la mairie"
    )
    horaires_mairie = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Horaires de la mairie"
    )
    
    # Commentaires
    commentaires_generaux_commune = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaires généraux sur la commune"
    )
    
    # Géométrie
    feature = models.OneToOneField(
        Feature,
        on_delete=models.CASCADE,
        related_name='commune',
        verbose_name="Entité géographique associée"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'communes'
        ordering = ['nom']
        verbose_name = "Commune"
        verbose_name_plural = "Communes"
        indexes = [
            models.Index(fields=['code_insee']),
            models.Index(fields=['nom']),
            models.Index(fields=['arrondissement']),
            models.Index(fields=['canton']),
            models.Index(fields=['type_doc_urba_approuve']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if self.superficie_km2 and self.superficie_km2 <= 0:
            raise ValidationError({'superficie_km2': 'La superficie doit être positive.'})

    def __str__(self):
        return f"{self.nom} ({self.code_insee})"

class UGE(models.Model):
    """
    Modèle représentant les Unités de Gestion d'Eau (UGE).
    
    Une UGE regroupe plusieurs communes pour la gestion de l'eau potable.
    Contient les informations de gestion, exploitation et réglementation.
    """
    
    # Types de compétences
    TYPE_COMPETENCE_CHOICES = [
        ('PRODUCTION', 'Production d\'eau potable'),
        ('DISTRIBUTION', 'Distribution d\'eau potable'),
        ('ASSAINISSEMENT', 'Assainissement'),
        ('GESTION', 'Gestion globale'),
    ]
    
    # Types de modes d'exploitation
    TYPE_MODE_EXPLOITATION_CHOICES = [
        ('REGIE', 'Régie directe'),
        ('DSP', 'Délégation de Service Public'),
        ('CONCESSION', 'Concession'),
        ('AFF_TERME', 'Affermage'),
        ('MIXTE', 'Mode mixte'),
    ]
    
    # Champs principaux
    code_uge = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code UGE",
        help_text="Identifiant unique de l'UGE"
    )
    nom_uge = models.CharField(
        max_length=200,
        verbose_name="Nom de l'UGE",
        db_index=True
    )

    # Identifiants SISPEA et type UGE (ajouts SECTION 1.1)
    code_sispea = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Code SISPEA",
        help_text="Code UGE dans la base SISPEA nationale (permet jointure avec données open data)"
    )
    type_uge = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Type de structure UGE",
        help_text="Type de structure : Commune, EPCI, Syndicat, Régie..."
    )
    prestation_service_externe = models.BooleanField(
        default=False,
        verbose_name="Prestation de service externe",
        help_text="Vrai si une prestation de service externe existe (hors DSP)"
    )
    
    # Gestion et exploitation
    maitre_ouvrage = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Maître d'ouvrage"
    )
    type_competence = models.CharField(
        max_length=20,
        choices=TYPE_COMPETENCE_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type de compétence"
    )
    type_mode_exploitation = models.CharField(
        max_length=20,
        choices=TYPE_MODE_EXPLOITATION_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type de mode d'exploitation"
    )
    exploitant = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Exploitant"
    )
    
    # Contrats et délégations
    date_fin_contrat_dsp = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin de contrat DSP",
        help_text="Date de fin de contrat de Délégation de Service Public"
    )
    date_fin_contrat_dsp_concession = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin de contrat DSP/concession"
    )
    prestation_service = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Prestation de service"
    )
    nature_prestation_service = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Nature de la prestation de service"
    )
    date_fin_contrat_prestation_service = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date de fin de contrat de prestation de service"
    )
    
    # Caractéristiques territoriales
    zone_homogene = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Zone homogène"
    )
    
    # Période de validité
    date_debut_validite_uge = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date de début de validité de l'UGE"
    )
    date_fin_validite_uge = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date de fin de validité de l'UGE"
    )
    
    # Documents réglementaires
    reglement_service = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Règlement de service"
    )
    plan_secours_aep = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Plan de secours AEP"
    )
    date_plan_secours_aep = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date du plan de secours AEP"
    )
    
    # Commentaires et analyses
    comment_generaux_uge = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaires généraux sur l'UGE"
    )
    comment_princip_fonctionnement = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire principal de fonctionnement"
    )
    comment_difficulte_exploitation = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire sur les difficultés d'exploitation"
    )
    comment_difficulte_satisf_besoins = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire sur les difficultés à satisfaire les besoins"
    )
    comment_conflit_usage_ressource = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire sur les conflits d'usage de la ressource"
    )
    comment_retour_exp_crises = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire sur le retour d'expérience des crises"
    )
    comment_proj_souhait_uge = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire sur les projets souhaités pour l'UGE"
    )
    comment_politique_tarification = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire sur la politique de tarification"
    )
    comment_politique_economies_eau = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire sur la politique d'économies d'eau"
    )
    
    # Géométrie
    feature = models.OneToOneField(
        Feature,
        on_delete=models.CASCADE,
        related_name='uge',
        verbose_name="Entité géographique associée",
        null=True,
        blank=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'uges'
        ordering = ['nom_uge']
        verbose_name = "Unité de Gestion d'Eau (UGE)"
        verbose_name_plural = "Unités de Gestion d'Eau (UGE)"
        indexes = [
            models.Index(fields=['code_uge']),
            models.Index(fields=['nom_uge']),
            models.Index(fields=['type_competence']),
            models.Index(fields=['type_mode_exploitation']),
            models.Index(fields=['maitre_ouvrage']),
            models.Index(fields=['exploitant']),
            models.Index(fields=['date_debut_validite_uge']),
            models.Index(fields=['date_fin_validite_uge']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.date_debut_validite_uge and self.date_fin_validite_uge and 
            self.date_debut_validite_uge > self.date_fin_validite_uge):
            raise ValidationError({
                'date_fin_validite_uge': 'La date de fin doit être postérieure à la date de début.'
            })

    def __str__(self):
        return f"{self.nom_uge} ({self.code_uge})"

class UDI(models.Model):
    """
    Modèle représentant les Unités de Distribution d'Eau (UDI).
    
    Une UDI est une unité de distribution qui peut être associée à une UGE.
    Contient les informations de distribution et de nature de l'eau.
    """
    
    # Types d'usage direct
    TYPE_USAGE_DIRECT_CHOICES = [
        ('AEP', 'Alimentation en Eau Potable'),
        ('INDUSTRIEL', 'Usage industriel'),
        ('AGRICOLE', 'Usage agricole'),
        ('MIXTE', 'Usage mixte'),
    ]
    
    # États d'activité INS
    TYPE_ETAT_ACTIVITE_INS_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('EN_CONSTRUCTION', 'En construction'),
        ('EN_DEMOLITION', 'En démolition'),
        ('PROJET', 'Projet'),
    ]
    
    # Types de nature d'eau
    TYPE_NATURE_EAU_CHOICES = [
        ('EAU_BRUTE', 'Eau brute'),
        ('EAU_TRAITEE', 'Eau traitée'),
        ('EAU_POTABLE', 'Eau potable'),
        ('EAU_DISTRIBUTEE', 'Eau distribuée'),
    ]
    
    # Champs principaux
    code_ins_udi = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Code INS UDI",
        help_text="Identifiant INS unique de l'UDI"
    )
    nom_ins_udi = models.CharField(
        max_length=500, 
        verbose_name="Nom INS UDI",
        db_index=True
    )
    
    # Relation avec UGE
    uge = models.ForeignKey(
        UGE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='udis',
        verbose_name="UGE associée"
    )
    
    # Période de validité
    date_debut_validite_udi = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date de début de validité de l'UDI"
    )
    date_fin_validite_udi = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date de fin de validité de l'UDI"
    )
    
    # Caractéristiques techniques
    type_usage_direct = models.CharField(
        max_length=20,
        choices=TYPE_USAGE_DIRECT_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type d'usage direct"
    )
    type_etat_activite_ins = models.CharField(
        max_length=20,
        choices=TYPE_ETAT_ACTIVITE_INS_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type/État d'activité INS"
    )
    type_nature_eau = models.CharField(
        max_length=20,
        choices=TYPE_NATURE_EAU_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type/Nature de l'eau"
    )
    
    # Commentaires
    comment_udi = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaires sur l'UDI"
    )

    nom_quartier = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Nom du quartier desservi"
    )

    # Caractéristiques complémentaires (ajouts SECTION 1.3)
    population_desservie = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Population desservie",
        help_text="Population max desservie par cette UDI (peut différer de la pop communale)"
    )
    type_distribution = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Type de distribution",
        help_text="Type : Gravitaire, Refoulement, Mixte"
    )

    communes = models.ManyToManyField(
        Commune,
        related_name='udis',
        verbose_name="Communes desservies"
    )
    
    # Géométrie
    feature = models.OneToOneField(
        Feature,
        on_delete=models.CASCADE,
        related_name='udi',
        verbose_name="Entité géographique associée",
        null=True,
        blank=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'udis'
        ordering = ['nom_ins_udi']
        verbose_name = "Unité de Distribution d'Eau (UDI)"
        verbose_name_plural = "Unités de Distribution d'Eau (UDI)"
        indexes = [
            models.Index(fields=['code_ins_udi']),
            models.Index(fields=['nom_ins_udi']),
            models.Index(fields=['uge']),
            models.Index(fields=['type_usage_direct']),
            models.Index(fields=['type_etat_activite_ins']),
            models.Index(fields=['type_nature_eau']),
            models.Index(fields=['date_debut_validite_udi']),
            models.Index(fields=['date_fin_validite_udi']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.date_debut_validite_udi and self.date_fin_validite_udi and 
            self.date_debut_validite_udi > self.date_fin_validite_udi):
            raise ValidationError({
                'date_fin_validite_udi': 'La date de fin doit être postérieure à la date de début.'
            })

    def __str__(self):
        return f"{self.nom_ins_udi} ({self.code_ins_udi})"

class Captage(models.Model):
    """
    Modèle représentant les captages d'eau.
    
    Un captage est un ouvrage de prélèvement d'eau, associé à une UGE
    et situé dans une commune. Contient toutes les informations techniques,
    réglementaires et de production.
    """
    
    # Types d'usage direct
    TYPE_USAGE_DIRECT_CHOICES = [
        ('AEP', 'Alimentation en Eau Potable'),
        ('INDUSTRIEL', 'Usage industriel'),
        ('AGRICOLE', 'Usage agricole'),
        ('MIXTE', 'Usage mixte'),
    ]
    
    # États d'activité INS
    TYPE_ETAT_ACTIVITE_INS_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('EN_CONSTRUCTION', 'En construction'),
        ('EN_DEMOLITION', 'En démolition'),
        ('PROJET', 'Projet'),
    ]
    
    # Types de captage
    TYPE_CAPTAGE_CHOICES = [
        ('FORAGE', 'Forage'),
        ('PUITS', 'Puits'),
        ('SOURCE', 'Source'),
        ('DRAINAGE', 'Drainage'),
        ('AUTRE', 'Autre'),
    ]
    
    # Types de nature d'eau
    TYPE_NATURE_EAU_CHOICES = [
        ('EAU_BRUTE', 'Eau brute'),
        ('EAU_TRAITEE', 'Eau traitée'),
        ('EAU_POTABLE', 'Eau potable'),
    ]
    
    # États de procédure de protection
    TYPE_ETAT_PROCED_PROTECTION_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('APPROUVEE', 'Approuvée'),
        ('ABANDONNEE', 'Abandonnée'),
        ('AUCUNE', 'Aucune'),
    ]
    
    # Champs principaux
    code_ins_captage = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Code INS captage",
        help_text="Identifiant INS unique du captage"
    )
    nom_captage = models.CharField(
        max_length=200, 
        verbose_name="Nom du captage",
        db_index=True
    )
    
    # Codes de référence
    code_bss = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Code BSS",
        help_text="Code Banque du Sous-Sol"
    )
    code_prelev_ae = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Code prélèvement A/E"
    )
    code_siseaux = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Code SISE-EAUX",
        help_text="Code SISE-EAUX national du captage (base ARS)"
    )
    autre_libelle_captage = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Autre libellé du captage"
    )
    
    # Relations
    uge = models.ForeignKey(
        UGE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='captages',
        verbose_name="UGE associée"
    )
    commune_implantation = models.ForeignKey(
        Commune,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='captages',
        verbose_name="Commune d'implantation"
    )
    
    # Période de validité
    date_debut_validite_captage = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date de début de validité du captage"
    )
    date_fin_validite_captage = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Date de fin de validité du captage"
    )
    
    # Caractéristiques techniques
    type_usage_direct = models.CharField(
        max_length=20,
        choices=TYPE_USAGE_DIRECT_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type d'usage direct"
    )
    type_etat_activite_ins = models.CharField(
        max_length=20,
        choices=TYPE_ETAT_ACTIVITE_INS_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type/État d'activité INS"
    )
    code_utilisation_ouvrage = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Utilisation de l'ouvrage"
    )
    type_nature_eau = models.CharField(
        max_length=20,
        choices=TYPE_NATURE_EAU_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type/Nature de l'eau"
    )
    type_captage = models.CharField(
        max_length=20,
        choices=TYPE_CAPTAGE_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Type de captage"
    )
    
    # Caractéristiques physiques
    altitude_m_ngf = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        blank=True, 
        null=True, 
        verbose_name="Altitude (m NGF)",
        help_text="Altitude en mètres Nivellement Général de la France"
    )
    description_ouvrage = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Description de l'ouvrage"
    )
    
    # Protection et réglementation
    type_etat_proced_protection = models.CharField(
        max_length=20,
        choices=TYPE_ETAT_PROCED_PROTECTION_CHOICES,
        blank=True,
        null=True,
        verbose_name="Type/État de procédure de protection"
    )
    perimetre_protection_declare = models.BooleanField(
        default=False,
        verbose_name="Périmètre de protection déclaré",
        help_text="Vrai si DUP (Déclaration Utilité Publique) effectuée"
    )
    date_rapport_hydro = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date du rapport hydrogéologique"
    )
    date_delib_proc_protection = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de délibération de procédure de protection"
    )
    date_recevabilite_dup = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de recevabilité DUP"
    )
    date_declaration_dup = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de déclaration DUP",
        help_text="Date de la Déclaration d'Utilité Publique"
    )
    date_dup = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de DUP"
    )
    
    # Capacités et débits (en DecimalField pour la précision)
    debit_autorise_m3_j = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Débit autorisé (m³/j)",
        help_text="Débit de prélèvement autorisé en m³ par jour",
        validators=[MinValueValidator(Decimal('0'))]
    )
    debit_equipement_m3_h = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Débit d'équipement (m³/h)",
        help_text="Débit de l'équipement de pompage en m³ par heure",
        validators=[MinValueValidator(Decimal('0'))]
    )
    q_dup_l_s = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Quantité DUP (L/s)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    q_dup_m3_h = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Quantité DUP (m³/h)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    q_dup_m3_j = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Quantité DUP (m³/j)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    q_dup_m3_an = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Quantité DUP (m³/an)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Capacités de production
    capa_prod_captage_m3_h = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Capacité de production du captage (m³/h)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    potentiel_prod_captage_m3_h = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Potentiel de production du captage (m³/h)",
        validators=[MinValueValidator(Decimal('0'))]
    )

    # Ressource et vulnérabilité (ajouts SECTION 1.2)
    code_masse_eau_souterraine = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Code masse d'eau souterraine",
        help_text="Code de la masse d'eau DCE (Directive Cadre sur l'Eau)"
    )
    vulnerabilite_ressource = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Vulnérabilité de la ressource",
        help_text="Échelle 1-5 : 1=Très faible, 5=Très élevée",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    etat_ouvrage = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="État de l'ouvrage",
        help_text="État général de l'ouvrage : Bon, Moyen, Mauvais, À rénover"
    )
    
    # Équipements
    nb_pompes = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        verbose_name="Nombre de pompes"
    )
    existence_telegestion = models.BooleanField(
        default=False,
        verbose_name="Existence de la télégestion"
    )
    existence_alarme_anti_intrusion = models.BooleanField(
        default=False,
        verbose_name="Existence d'alarme anti-intrusion"
    )
    existence_report_alarme = models.BooleanField(
        default=False,
        verbose_name="Existence de report d'alarme"
    )
    
    # Commentaires
    comment_status_ouvrage = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaire sur le statut de l'ouvrage"
    )
    comment_environ_risques = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaires sur l'environnement et les risques"
    )
    comment_problemes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaires sur les problèmes"
    )
    comment_generaux_captage = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Commentaires généraux sur le captage"
    )
    
    # Géométrie
    feature = models.OneToOneField(
        Feature,
        on_delete=models.CASCADE,
        related_name='captage',
        verbose_name="Entité géographique associée"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de modification"
    )

    class Meta:
        db_table = 'captages'
        ordering = ['nom_captage']
        verbose_name = "Captage d'eau"
        verbose_name_plural = "Captages d'eau"
        indexes = [
            models.Index(fields=['code_ins_captage']),
            models.Index(fields=['nom_captage']),
            models.Index(fields=['uge']),
            models.Index(fields=['commune_implantation']),
            models.Index(fields=['type_usage_direct']),
            models.Index(fields=['type_etat_activite_ins']),
            models.Index(fields=['type_captage']),
            models.Index(fields=['type_nature_eau']),
            models.Index(fields=['date_debut_validite_captage']),
            models.Index(fields=['date_fin_validite_captage']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.date_debut_validite_captage and self.date_fin_validite_captage and 
            self.date_debut_validite_captage > self.date_fin_validite_captage):
            raise ValidationError({
                'date_fin_validite_captage': 'La date de fin doit être postérieure à la date de début.'
            })

    def __str__(self):
        return f"{self.nom_captage} ({self.code_ins_captage})"


# ============================================================================
# SECTION 2 : TABLES DE LIAISON (RELATIONS MANY-TO-MANY)
# ============================================================================

class CommuneUGE(models.Model):
    """
    Table de jointure Communes ↔ UGE (relation Many-to-Many avec attributs).

    Source : Fichier UGE/AEP.xlsx (colonne COMPETENCE_AEP).
    Permet de savoir quelle commune adhère à quelle UGE, avec quel pourcentage.
    USAGE : Pour générer la géométrie d'une UGE, faire ST_Union() des géométries des communes liées.

    Une commune peut adhérer à plusieurs UGE (partiellement ou totalement).
    Cas réel : Une commune peut être desservie à 80% par UGE_A et 20% par UGE_B.
    """

    commune = models.ForeignKey(
        Commune,
        on_delete=models.CASCADE,
        related_name='adhesions_uge',
        verbose_name="Commune"
    )
    uge = models.ForeignKey(
        UGE,
        on_delete=models.CASCADE,
        related_name='adhesions_communes',
        verbose_name="UGE"
    )

    pourcentage_adhesion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        verbose_name="Pourcentage d'adhésion",
        help_text="Pourcentage du territoire communal desservi par cette UGE (défaut 100%). Ex : 70% par Syndicat A, 30% par Syndicat B.",
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))]
    )
    date_debut_adhesion = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de début d'adhésion"
    )
    date_fin_adhesion = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin d'adhésion"
    )

    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'communes_uges'
        verbose_name = "Adhésion Commune-UGE"
        verbose_name_plural = "Adhésions Communes-UGE"
        unique_together = [['commune', 'uge', 'date_debut_adhesion']]
        indexes = [
            models.Index(fields=['commune']),
            models.Index(fields=['uge']),
            models.Index(fields=['date_debut_adhesion', 'date_fin_adhesion']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.date_debut_adhesion and self.date_fin_adhesion and
            self.date_debut_adhesion > self.date_fin_adhesion):
            raise ValidationError({
                'date_fin_adhesion': 'La date de fin doit être postérieure à la date de début.'
            })

    def __str__(self):
        return f"{self.commune.nom} → {self.uge.nom_uge} ({self.pourcentage_adhesion}%)"


class UGECaptage(models.Model):
    """
    Table de jointure UGE ↔ Captages (relation Many-to-Many avec attributs).

    Source : Fichier SISPEA "ouvrage" + sdaep.captage_udi.
    Permet de savoir quels captages alimentent quelle UGE.
    Type de lien : principal (usage permanent), secours (usage occasionnel),
                   interconnexion (via une autre UGE).

    Un captage peut alimenter plusieurs UGE (rare mais existe).
    Cas réel : Un captage en limite départementale alimente 2 syndicats.
    """

    TYPE_LIEN_CHOICES = [
        ('principal', 'Principal'),
        ('secours', 'Secours'),
        ('interconnexion', 'Interconnexion'),
    ]

    uge = models.ForeignKey(
        UGE,
        on_delete=models.CASCADE,
        related_name='liaisons_captages',
        verbose_name="UGE"
    )
    captage = models.ForeignKey(
        Captage,
        on_delete=models.CASCADE,
        related_name='liaisons_uges',
        verbose_name="Captage"
    )

    type_lien = models.CharField(
        max_length=50,
        choices=TYPE_LIEN_CHOICES,
        default='principal',
        verbose_name="Type de lien"
    )
    date_debut_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de début de validité"
    )
    date_fin_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin de validité"
    )

    pourcentage_production = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Pourcentage de production",
        help_text="Pourcentage de la production de l'UGE assuré par ce captage. Ex : 50%, 30%, 20%",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'uges_captages'
        verbose_name = "Liaison UGE-Captage"
        verbose_name_plural = "Liaisons UGE-Captages"
        unique_together = [['uge', 'captage', 'date_debut_validite']]
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['captage']),
            models.Index(fields=['type_lien']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.date_debut_validite and self.date_fin_validite and
            self.date_debut_validite > self.date_fin_validite):
            raise ValidationError({
                'date_fin_validite': 'La date de fin doit être postérieure à la date de début.'
            })

    def __str__(self):
        return f"{self.uge.nom_uge} ← {self.captage.nom_captage} ({self.type_lien})"


# ============================================================================
# SECTION 3 : OUVRAGES COMPLÉMENTAIRES (MANQUANTS ACTUELLEMENT)
# ============================================================================

class StationTraitement(models.Model):
    """
    Modèle représentant les stations de traitement de l'eau potable (TTP).

    Source : SDAEP Phase 1 fichier "04 - captages AEP.xlsx" (stations liées aux captages).
    Utilité : Inventaire des ouvrages de potabilisation, suivi de leur état et capacité.
    Lien cartographique : feature_id pointe vers features (géométrie Point).
    """

    code_ins_ttp = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code INS TTP",
        help_text="Identifiant unique de la station de traitement"
    )
    nom_station = models.CharField(
        max_length=200,
        verbose_name="Nom de la station",
        db_index=True
    )

    uge = models.ForeignKey(
        UGE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stations_traitement',
        verbose_name="UGE"
    )
    commune_implantation = models.ForeignKey(
        Commune,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stations_traitement',
        verbose_name="Commune d'implantation"
    )

    type_traitement = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Type de traitement",
        help_text="Type principal : Chloration, Filtration, UV, Déferrisation, Démanganisation, Osmose inverse"
    )
    type_usage_direct = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Type d'usage direct"
    )
    type_etat_activite = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="État d'activité"
    )

    capacite_traitement_m3_j = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Capacité de traitement (m³/j)"
    )
    date_mise_service = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de mise en service"
    )
    altitude_m_ngf = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Altitude (m NGF)"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    feature = models.OneToOneField(
        Feature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='station_traitement',
        verbose_name="Entité géographique associée"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'stations_traitement'
        verbose_name = "Station de traitement"
        verbose_name_plural = "Stations de traitement"
        ordering = ['nom_station']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['commune_implantation']),
            models.Index(fields=['type_etat_activite']),
        ]

    def __str__(self):
        return f"{self.nom_station} ({self.code_ins_ttp})"


class StationPompage(models.Model):
    """
    Modèle représentant les stations de pompage (surpresseurs, reprises).

    Source : SDAEP Phase 1.
    Utilité : Inventaire des ouvrages de relevage nécessaires au réseau.
    Type : Reprise (pomper depuis un réservoir bas vers un haut),
           Surpression (augmenter la pression).
    """

    code_station = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code station",
        help_text="Identifiant unique de la station de pompage"
    )
    nom_station = models.CharField(
        max_length=200,
        verbose_name="Nom de la station",
        db_index=True
    )

    uge = models.ForeignKey(
        UGE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stations_pompage',
        verbose_name="UGE"
    )
    commune_implantation = models.ForeignKey(
        Commune,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stations_pompage',
        verbose_name="Commune d'implantation"
    )

    type_station = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Type de station",
        help_text="Reprise, Surpression, Autre"
    )
    type_etat_activite = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="État d'activité"
    )

    nb_pompes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de pompes",
        validators=[MinValueValidator(1)]
    )
    capacite_totale_m3_h = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Capacité totale (m³/h)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    altitude_m_ngf = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Altitude (m NGF)"
    )

    existence_telegestion = models.BooleanField(
        default=False,
        verbose_name="Existence de la télégestion"
    )
    existence_alarme = models.BooleanField(
        default=False,
        verbose_name="Existence d'alarme"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    feature = models.OneToOneField(
        Feature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='station_pompage',
        verbose_name="Entité géographique associée"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'stations_pompage'
        verbose_name = "Station de pompage"
        verbose_name_plural = "Stations de pompage"
        ordering = ['nom_station']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['commune_implantation']),
        ]

    def __str__(self):
        return f"{self.nom_station} ({self.code_station})"


class Reservoir(models.Model):
    """
    Modèle représentant les réservoirs de stockage d'eau potable.

    Source : SDAEP Phase 1.
    Utilité : Calcul de l'autonomie et de la sécurisation (volume stocké / consommation journalière).
    Type : Enterré, Semi-enterré, Sur tour, Château d'eau.
    """

    TYPE_RESERVOIR_CHOICES = [
        ('ENT', 'Enterré'),
        ('SEN', 'Semi-enterré'),
        ('TOU', 'Sur tour'),
        ('CHA', 'Château d\'eau'),
    ]

    code_reservoir = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code réservoir",
        help_text="Identifiant unique du réservoir"
    )
    nom_reservoir = models.CharField(
        max_length=200,
        verbose_name="Nom du réservoir",
        db_index=True
    )

    uge = models.ForeignKey(
        UGE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservoirs',
        verbose_name="UGE"
    )
    commune_implantation = models.ForeignKey(
        Commune,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservoirs',
        verbose_name="Commune d'implantation"
    )

    type_reservoir = models.CharField(
        max_length=50,
        choices=TYPE_RESERVOIR_CHOICES,
        blank=True,
        null=True,
        verbose_name="Type de réservoir"
    )
    type_etat_activite = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="État d'activité"
    )

    volume_total_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume total (m³)",
        validators=[MinValueValidator(1)]
    )
    volume_utile_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume utile (m³)",
        help_text="Volume réellement utilisable (= volume total - volume mort - volume incendie). Utilisé pour les calculs d'autonomie."
    )
    volume_incendie_m3 = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Volume incendie (m³)"
    )
    altitude_m_ngf = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Altitude (m NGF)"
    )

    nb_cuves = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de cuves"
    )
    date_derniere_vidange = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de dernière vidange"
    )
    frequence_nettoyage = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Fréquence de nettoyage",
        help_text="Annuelle, Bisannuelle, etc."
    )

    existence_telegestion = models.BooleanField(
        default=False,
        verbose_name="Existence de la télégestion"
    )
    existence_alarme = models.BooleanField(
        default=False,
        verbose_name="Existence d'alarme"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    feature = models.OneToOneField(
        Feature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservoir',
        verbose_name="Entité géographique associée"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'reservoirs'
        verbose_name = "Réservoir"
        verbose_name_plural = "Réservoirs"
        ordering = ['nom_reservoir']
        indexes = [
            models.Index(fields=['uge']),
            models.Index(fields=['commune_implantation']),
            models.Index(fields=['type_reservoir']),
        ]

    def __str__(self):
        return f"{self.nom_reservoir} ({self.code_reservoir})"


class MelangeCaptage(models.Model):
    """
    Modèle représentant les mélanges de captages (MCA).

    Source : SDAEP 2015.
    Utilité : Traçabilité des mélanges d'eau de qualité différente.
    Mélanges de Captages (MCA) = installations où plusieurs captages sont mélangés.
    Lien : Voir table MelangeCaptageDetail pour savoir quels captages sont mélangés.
    """

    code_ins_mca = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code INS MCA",
        help_text="Identifiant unique du mélange de captages"
    )
    nom_melange = models.CharField(
        max_length=200,
        verbose_name="Nom du mélange",
        db_index=True
    )

    uge = models.ForeignKey(
        UGE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='melanges_captages',
        verbose_name="UGE"
    )

    date_debut_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de début de validité"
    )
    date_fin_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin de validité"
    )
    type_etat_activite = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="État d'activité"
    )

    debit_nominal_m3_j = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Débit nominal (m³/j)",
        validators=[MinValueValidator(Decimal('0'))]
    )
    altitude_m_ngf = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Altitude (m NGF)"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    feature = models.OneToOneField(
        Feature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='melange_captage',
        verbose_name="Entité géographique associée"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'melanges_captages'
        verbose_name = "Mélange de captages"
        verbose_name_plural = "Mélanges de captages"
        ordering = ['nom_melange']
        indexes = [
            models.Index(fields=['uge']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.date_debut_validite and self.date_fin_validite and
            self.date_debut_validite > self.date_fin_validite):
            raise ValidationError({
                'date_fin_validite': 'La date de fin doit être postérieure à la date de début.'
            })

    def __str__(self):
        return f"{self.nom_melange} ({self.code_ins_mca})"


class MelangeCaptageDetail(models.Model):
    """
    Détail des captages participant à un mélange (MCA).

    Permet de savoir quel captage contribue à hauteur de quel % dans le mélange.
    """

    melange = models.ForeignKey(
        MelangeCaptage,
        on_delete=models.CASCADE,
        related_name='details_captages',
        verbose_name="Mélange de captages"
    )
    captage = models.ForeignKey(
        Captage,
        on_delete=models.CASCADE,
        related_name='melanges',
        verbose_name="Captage"
    )

    date_debut_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de début de validité"
    )
    date_fin_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin de validité"
    )

    pourcentage_contribution = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Pourcentage de contribution",
        help_text="Pourcentage de contribution du captage dans le mélange",
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = 'melanges_captages_details'
        verbose_name = "Détail mélange captage"
        verbose_name_plural = "Détails mélanges captages"
        unique_together = [['melange', 'captage', 'date_debut_validite']]
        indexes = [
            models.Index(fields=['melange']),
            models.Index(fields=['captage']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if (self.date_debut_validite and self.date_fin_validite and
            self.date_debut_validite > self.date_fin_validite):
            raise ValidationError({
                'date_fin_validite': 'La date de fin doit être postérieure à la date de début.'
            })

    def __str__(self):
        return f"{self.melange.nom_melange} ← {self.captage.nom_captage}"


class Interconnexion(models.Model):
    """
    Modèle représentant les interconnexions entre UGE (ventes/achats d'eau).

    Source : SDAEP Phase 1 fichier "interconnexions".
    Utilité : Suivi des échanges d'eau, calcul de la dépendance/autonomie.
    Type : Permanente (usage quotidien), Secours (usage exceptionnel),
           Saisonnière (été uniquement).
    """

    TYPE_UTILISATION_CHOICES = [
        ('PERMANENTE', 'Permanente'),
        ('SECOURS', 'Secours'),
        ('SAISONNIERE', 'Saisonnière'),
    ]

    code_interconnexion = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Code interconnexion"
    )
    nom_interconnexion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nom de l'interconnexion"
    )

    uge_vendeuse = models.ForeignKey(
        UGE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interconnexions_vendues',
        verbose_name="UGE vendeuse"
    )
    uge_acheteuse = models.ForeignKey(
        UGE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interconnexions_achetees',
        verbose_name="UGE acheteuse"
    )

    type_utilisation = models.CharField(
        max_length=30,
        choices=TYPE_UTILISATION_CHOICES,
        blank=True,
        null=True,
        verbose_name="Type d'utilisation"
    )
    date_debut_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de début de validité"
    )
    date_fin_validite = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin de validité"
    )

    diametre_mm = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Diamètre (mm)"
    )
    debit_max_convention_m3_j = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Débit max convention (m³/j)",
        help_text="Débit maximum autorisé par la convention entre les deux parties"
    )
    debit_max_technique_m3_j = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Débit max technique (m³/j)",
        help_text="Débit maximum technique de la canalisation (peut être > débit convention)"
    )

    existence_compteur = models.BooleanField(
        default=False,
        verbose_name="Existence d'un compteur"
    )
    existence_telegestion = models.BooleanField(
        default=False,
        verbose_name="Existence de la télégestion"
    )

    convention_signee = models.BooleanField(
        default=False,
        verbose_name="Convention signée"
    )
    date_convention = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de la convention"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    commentaires = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    feature = models.OneToOneField(
        Feature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interconnexion',
        verbose_name="Entité géographique associée"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'interconnexions'
        verbose_name = "Interconnexion"
        verbose_name_plural = "Interconnexions"
        ordering = ['nom_interconnexion']
        indexes = [
            models.Index(fields=['uge_vendeuse']),
            models.Index(fields=['uge_acheteuse']),
            models.Index(fields=['type_utilisation']),
        ]

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if self.uge_vendeuse and self.uge_acheteuse and self.uge_vendeuse == self.uge_acheteuse:
            raise ValidationError({
                'uge_acheteuse': 'L\'UGE acheteuse ne peut pas être la même que l\'UGE vendeuse.'
            })
        if (self.date_debut_validite and self.date_fin_validite and
            self.date_debut_validite > self.date_fin_validite):
            raise ValidationError({
                'date_fin_validite': 'La date de fin doit être postérieure à la date de début.'
            })

    def __str__(self):
        if self.uge_vendeuse and self.uge_acheteuse:
            return f"{self.uge_vendeuse.nom_uge} → {self.uge_acheteuse.nom_uge}"
        return f"Interconnexion {self.code_interconnexion}"
