"""
Configuration de l'interface d'administration Django pour l'Observatoire SDAEP.

Enregistre les modèles de l'application avec leurs interfaces d'administration personnalisées.
"""

from django.contrib.gis import admin
from .models import (
    Layer, Feature, Arrondissement, Canton, Commune,
    UGE, UDI, Captage
)


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les couches SIG.

    Permet de gérer les couches de données géographiques avec visualisation
    du nombre d'entités et filtres par type de géométrie.
    """
    list_display = ['name', 'geometry_type', 'feature_count', 'visible', 'created_at']
    list_filter = ['geometry_type', 'visible']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def feature_count(self, obj):
        """Retourne le nombre d'entités associées à la couche."""
        return obj.features.count()
    feature_count.short_description = 'Nombre d\'entités'


@admin.register(Feature)
class FeatureAdmin(admin.GISModelAdmin):
    """
    Interface d'administration pour les entités géographiques.

    Utilise GISModelAdmin pour permettre la visualisation et l'édition
    des géométries directement dans l'interface d'administration.
    """
    list_display = ['id', 'layer', 'get_identifier', 'created_at']
    list_filter = ['layer']

    def get_identifier(self, obj):
        """
        Retourne l'identifiant de l'entité via son modèle associé.

        L'identifiant dépend du type d'entité (Commune, Captage, etc.).
        """
        # Recherche du modèle associé via les relations OneToOne
        if hasattr(obj, 'commune'):
            return obj.commune.code_insee
        elif hasattr(obj, 'captage'):
            return obj.captage.code_ins_captage
        elif hasattr(obj, 'uge'):
            return obj.uge.code_uge
        elif hasattr(obj, 'udi'):
            return obj.udi.code_ins_udi
        elif hasattr(obj, 'canton'):
            return obj.canton.code_canton
        elif hasattr(obj, 'arrondissement'):
            return obj.arrondissement.code_arrondissement
        return 'N/A'
    get_identifier.short_description = 'Identifiant'


@admin.register(Arrondissement)
class ArrondissementAdmin(admin.GISModelAdmin):
    """
    Interface d'administration pour les arrondissements.

    Permet de gérer les arrondissements avec visualisation cartographique.
    """
    list_display = ['nom_arrondissement', 'code_arrondissement', 'commune_count', 'created_at']
    search_fields = ['nom_arrondissement', 'code_arrondissement']
    readonly_fields = ['created_at', 'updated_at']

    def commune_count(self, obj):
        """Retourne le nombre de communes dans l'arrondissement."""
        return obj.communes.count()
    commune_count.short_description = 'Nombre de communes'


@admin.register(Canton)
class CantonAdmin(admin.GISModelAdmin):
    """
    Interface d'administration pour les cantons.

    Permet de gérer les cantons avec visualisation cartographique.
    """
    list_display = ['nom_canton', 'code_canton', 'arrondissement', 'commune_count', 'created_at']
    list_filter = ['arrondissement']
    search_fields = ['nom_canton', 'code_canton']
    readonly_fields = ['created_at', 'updated_at']

    def commune_count(self, obj):
        """Retourne le nombre de communes dans le canton."""
        return obj.communes.count()
    commune_count.short_description = 'Nombre de communes'


@admin.register(Commune)
class CommuneAdmin(admin.GISModelAdmin):
    """
    Interface d'administration pour les communes.

    Permet de gérer les communes avec toutes leurs informations administratives
    et de visualisation cartographique.
    """
    list_display = [
        'nom', 'code_insee', 'arrondissement', 'canton',
        'type_doc_urba_approuve', 'superficie_km2', 'created_at'
    ]
    list_filter = [
        'arrondissement', 'canton', 'type_doc_urba_approuve',
        'type_doc_urba_en_cours'
    ]
    search_fields = ['nom', 'code_insee', 'nom_mairie']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations principales', {
            'fields': ('code_insee', 'nom', 'superficie_km2')
        }),
        ('Relations territoriales', {
            'fields': ('arrondissement', 'canton', 'zone_emploi')
        }),
        ('Urbanisme', {
            'fields': (
                'type_doc_urba_approuve', 'date_doc_urba_approuve',
                'type_doc_urba_en_cours', 'commentaires_generaux_urba_previs'
            )
        }),
        ('Mairie', {
            'fields': (
                'nom_mairie', 'adresse_mairie', 'code_postal_commune',
                'telephone_mairie', 'fax_mairie', 'email_mairie',
                'mobile_mairie', 'horaires_mairie'
            )
        }),
        ('Commentaires', {
            'fields': ('commentaires_generaux_commune',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UGE)
class UGEAdmin(admin.GISModelAdmin):
    """
    Interface d'administration pour les Unités de Gestion d'Eau (UGE).

    Permet de gérer les UGE avec toutes leurs informations de gestion,
    exploitation et visualisation cartographique.
    """
    list_display = [
        'nom_uge', 'code_uge', 'maitre_ouvrage', 'exploitant',
        'type_competence', 'type_mode_exploitation', 'created_at'
    ]
    list_filter = [
        'type_competence', 'type_mode_exploitation', 'maitre_ouvrage', 'exploitant'
    ]
    search_fields = ['nom_uge', 'code_uge', 'maitre_ouvrage', 'exploitant']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations principales', {
            'fields': ('code_uge', 'nom_uge')
        }),
        ('Gestion et exploitation', {
            'fields': (
                'maitre_ouvrage', 'type_competence', 'type_mode_exploitation',
                'exploitant', 'zone_homogene'
            )
        }),
        ('Contrats', {
            'fields': (
                'date_fin_contrat_dsp_concession', 'prestation_service',
                'nature_prestation_service', 'date_fin_contrat_prestation_service'
            )
        }),
        ('Validité', {
            'fields': ('date_debut_validite_uge', 'date_fin_validite_uge')
        }),
        ('Documents réglementaires', {
            'fields': (
                'reglement_service', 'plan_secours_aep', 'date_plan_secours_aep'
            )
        }),
        ('Commentaires', {
            'fields': (
                'comment_generaux_uge', 'comment_princip_fonctionnement',
                'comment_difficulte_exploitation', 'comment_difficulte_satisf_besoins',
                'comment_conflit_usage_ressource', 'comment_retour_exp_crises',
                'comment_proj_souhait_uge', 'comment_politique_tarification',
                'comment_politique_economies_eau'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UDI)
class UDIAdmin(admin.GISModelAdmin):
    """
    Interface d'administration pour les Unités de Distribution d'Eau (UDI).

    Permet de gérer les UDI avec leurs informations de distribution
    et visualisation cartographique.
    """
    list_display = [
        'nom_ins_udi', 'code_ins_udi', 'uge', 'type_usage_direct',
        'type_etat_activite_ins', 'type_nature_eau', 'created_at'
    ]
    list_filter = [
        'uge', 'type_usage_direct', 'type_etat_activite_ins', 'type_nature_eau'
    ]
    search_fields = ['nom_ins_udi', 'code_ins_udi']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations principales', {
            'fields': ('code_ins_udi', 'nom_ins_udi', 'uge')
        }),
        ('Caractéristiques techniques', {
            'fields': (
                'type_usage_direct', 'type_etat_activite_ins', 'type_nature_eau'
            )
        }),
        ('Validité', {
            'fields': ('date_debut_validite_udi', 'date_fin_validite_udi')
        }),
        ('Commentaires', {
            'fields': ('comment_udi',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Captage)
class CaptageAdmin(admin.GISModelAdmin):
    """
    Interface d'administration pour les captages d'eau.

    Permet de gérer les captages avec toutes leurs informations techniques,
    réglementaires et visualisation cartographique.
    """
    list_display = [
        'nom_captage', 'code_ins_captage', 'uge', 'commune_implantation',
        'type_captage', 'type_etat_activite_ins', 'type_etat_proced_protection', 'created_at'
    ]
    list_filter = [
        'uge', 'commune_implantation', 'type_captage', 'type_usage_direct',
        'type_etat_activite_ins', 'type_nature_eau', 'type_etat_proced_protection'
    ]
    search_fields = [
        'nom_captage', 'code_ins_captage', 'code_bss', 'code_prelev_ae', 'autre_libelle_captage'
    ]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations principales', {
            'fields': (
                'code_ins_captage', 'nom_captage', 'code_bss', 'code_prelev_ae',
                'autre_libelle_captage'
            )
        }),
        ('Relations', {
            'fields': ('uge', 'commune_implantation')
        }),
        ('Caractéristiques techniques', {
            'fields': (
                'type_usage_direct', 'type_etat_activite_ins', 'code_utilisation_ouvrage',
                'type_nature_eau', 'type_captage', 'altitude_m_ngf', 'description_ouvrage'
            )
        }),
        ('Validité', {
            'fields': ('date_debut_validite_captage', 'date_fin_validite_captage')
        }),
        ('Protection et réglementation', {
            'fields': (
                'type_etat_proced_protection', 'date_rapport_hydro',
                'date_delib_proc_protection', 'date_recevabilite_dup', 'date_dup'
            )
        }),
        ('Quantités DUP', {
            'fields': ('q_dup_l_s', 'q_dup_m3_h', 'q_dup_m3_j', 'q_dup_m3_an')
        }),
        ('Capacités de production', {
            'fields': ('capa_prod_captage_m3_h', 'potentiel_prod_captage_m3_h')
        }),
        ('Équipements', {
            'fields': (
                'nb_pompes', 'existence_telegestion', 'existence_alarme_anti_intrusion',
                'existence_report_alarme'
            )
        }),
        ('Commentaires', {
            'fields': (
                'comment_status_ouvrage', 'comment_environ_risques',
                'comment_problemes', 'comment_generaux_captage'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )
