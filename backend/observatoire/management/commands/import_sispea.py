"""
Management command pour importer les données SISPEA dans l'observatoire.

Ce script importe les données depuis le fichier Excel SISPEA (format .xls) :
- Feuille "Collectivités" : données des collectivités
- Feuille "Entités de gestion" : données UGE et indicateurs de performance
- Feuille "Ouvrages" : données sur les captages/ouvrages

Usage:
    python manage.py import_sispea <chemin_fichier.xls> [--departement=007] [--annee=2024]
"""

import pandas as pd
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from observatoire.models import (
    UGE, Captage, UGEPerformanceAnnuelle, CaptagePerformanceAnnuelle,
    Commune, SourceDonnees, ImportHistorique
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Importe les données SISPEA depuis un fichier Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            'fichier',
            type=str,
            help='Chemin vers le fichier Excel SISPEA (.xls)'
        )
        parser.add_argument(
            '--departement',
            type=str,
            default='007',
            help='Code département à importer (ex: 007 pour Ardèche). Format sur 3 chiffres.'
        )
        parser.add_argument(
            '--annee',
            type=int,
            default=2024,
            help='Année de référence des données (défaut: 2024)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule l\'import sans enregistrer en base'
        )
        parser.add_argument(
            '--feuille',
            type=str,
            choices=['collectivites', 'entites', 'ouvrages', 'all'],
            default='all',
            help='Feuille spécifique à importer (défaut: all)'
        )

    def handle(self, *args, **options):
        fichier = options['fichier']
        departement = options['departement']
        annee = options['annee']
        dry_run = options['dry_run']
        feuille = options['feuille']

        self.stdout.write(self.style.SUCCESS(f'Début de l\'import SISPEA depuis {fichier}'))
        self.stdout.write(f'Département: {departement}')
        self.stdout.write(f'Année: {annee}')

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE DRY-RUN : Aucune donnée ne sera enregistrée'))

        # Initialiser les compteurs
        stats = {
            'collectivites_created': 0,
            'collectivites_updated': 0,
            'uges_created': 0,
            'uges_updated': 0,
            'ouvrages_created': 0,
            'ouvrages_updated': 0,
            'performances_created': 0,
            'performances_updated': 0,
            'errors': 0
        }

        # Créer ou récupérer la source de données
        if not dry_run:
            source_donnees, _ = SourceDonnees.objects.get_or_create(
                code_source=f'SISPEA_{annee}',
                defaults={
                    'nom_source': f'SISPEA {annee} - Données nationales AEP',
                    'type_source': 'OFFICIELLE',
                    'organisme': 'SISPEA (Système d\'Information sur les Services Publics d\'Eau et d\'Assainissement)',
                    'date_reference': datetime(annee, 12, 31).date(),
                    'date_import': datetime.now().date(),
                    'fiabilite': 'Haute',
                    'description': 'Données officielles SISPEA sur l\'eau potable'
                }
            )

            # Créer l'historique d'import
            historique = ImportHistorique.objects.create(
                source=source_donnees,
                type_import='MAJ',
                statut_import='EN_COURS',
                fichier_source=fichier,
                table_cible='Collectivités, UGE, Captages, Performances'
            )
        else:
            historique = None

        try:
            # Import selon la feuille demandée
            if feuille in ['collectivites', 'all']:
                self.stdout.write(self.style.SUCCESS('\n' + '='*80))
                self.stdout.write(self.style.SUCCESS('IMPORT FEUILLE: Collectivités'))
                self.stdout.write(self.style.SUCCESS('='*80))
                df_collectivites = pd.read_excel(fichier, sheet_name='Collectivités')

                # Filtrer par département
                df_collectivites = df_collectivites[df_collectivites['DPT du siège de la coll.'] == departement]
                self.stdout.write(f'Nombre de collectivités trouvées: {len(df_collectivites)}')

                stats_coll = self._import_collectivites(df_collectivites, annee, dry_run)
                stats['uges_created'] += stats_coll['created']
                stats['uges_updated'] += stats_coll['updated']
                stats['performances_created'] += stats_coll['performances']
                stats['performances_updated'] += stats_coll['performances_updated']
                stats['errors'] += stats_coll['errors']

            if feuille in ['entites', 'all']:
                self.stdout.write(self.style.SUCCESS('\n' + '='*80))
                self.stdout.write(self.style.SUCCESS('IMPORT FEUILLE: Entités de gestion'))
                self.stdout.write(self.style.SUCCESS('='*80))
                df_entites = pd.read_excel(fichier, sheet_name='Entités de gestion')

                # Filtrer par département
                df_entites = df_entites[df_entites['DPT du siège de la coll.'] == departement]
                self.stdout.write(f'Nombre d\'entités de gestion trouvées: {len(df_entites)}')

                stats_uge = self._import_entites_gestion(df_entites, annee, dry_run)
                stats['uges_created'] += stats_uge['created']
                stats['uges_updated'] += stats_uge['updated']
                stats['performances_created'] += stats_uge['performances']
                stats['performances_updated'] += stats_uge['performances_updated']
                stats['errors'] += stats_uge['errors']

            if feuille in ['ouvrages', 'all']:
                self.stdout.write(self.style.SUCCESS('\n' + '='*80))
                self.stdout.write(self.style.SUCCESS('IMPORT FEUILLE: Ouvrages'))
                self.stdout.write(self.style.SUCCESS('='*80))
                df_ouvrages = pd.read_excel(fichier, sheet_name='Ouvrages')

                # Filtrer par département
                df_ouvrages = df_ouvrages[df_ouvrages['DPT du siège de la coll.'] == departement]
                self.stdout.write(f'Nombre d\'ouvrages trouvés: {len(df_ouvrages)}')

                stats_ouvrages = self._import_ouvrages(df_ouvrages, annee, dry_run)
                stats['ouvrages_created'] += stats_ouvrages['created']
                stats['ouvrages_updated'] += stats_ouvrages['updated']
                stats['errors'] += stats_ouvrages['errors']

            # Mettre à jour l'historique
            if not dry_run and historique:
                historique.statut_import = 'REUSSI'
                total_imports = (stats['collectivites_created'] + stats['uges_created'] +
                               stats['ouvrages_created'] + stats['performances_created'])
                historique.nb_lignes_importees = total_imports
                historique.nb_lignes_erreur = stats['errors']
                historique.save()

            # Afficher le résumé
            self._afficher_resume(stats, dry_run)

        except Exception as e:
            if not dry_run and historique:
                historique.statut_import = 'ERREUR'
                historique.log_import = str(e)
                historique.save()
            logger.error(f'Erreur lors de l\'import : {str(e)}', exc_info=True)
            raise CommandError(f'Erreur lors de l\'import : {str(e)}')

    def _import_collectivites(self, df_collectivites, annee, dry_run):
        """
        Importe les données de la feuille Collectivités.

        Pour chaque collectivité de type Commune :
        1. Crée ou met à jour une UGE correspondante
        2. Importe tous les indicateurs de performance dans UGEPerformanceAnnuelle
        """
        stats = {'created': 0, 'updated': 0, 'performances': 0, 'performances_updated': 0, 'errors': 0}

        for idx, row in df_collectivites.iterrows():
            try:
                # Données principales de la collectivité
                type_coll = str(row.get('Type collectivité', ''))
                nom_coll = str(row.get('Nom collectivité', ''))
                code_insee = str(row.get('N° INSEE si commune', ''))
                id_sispea_coll = row.get('Id SISPEA de la collectivité')

                # On traite uniquement les communes
                if type_coll.lower() != 'commune' or pd.isna(row.get('N° INSEE si commune')):
                    continue

                # Formatter le code INSEE (5 chiffres)
                if code_insee and code_insee != 'nan':
                    code_insee = code_insee.zfill(5)
                else:
                    continue

                if pd.isna(id_sispea_coll):
                    continue

                code_sispea = str(int(id_sispea_coll))

                if dry_run:
                    self.stdout.write(f'  [DRY-RUN] Collectivité: {nom_coll} ({code_insee}) → UGE SISPEA {code_sispea}')
                    stats['created'] += 1
                    stats['performances'] += 1
                else:
                    # Chercher ou créer l'UGE pour cette collectivité
                    uge_data = {
                        'code_sispea': code_sispea,
                        'nom_uge': nom_coll,
                        'code_uge': code_insee,  # On utilise le code INSEE comme code UGE
                        'maitre_ouvrage': nom_coll,
                        'type_uge': 'Commune',
                    }

                    # Compétences
                    if pd.notna(row.get('Production')) and str(row.get('Production')).lower() == 'oui':
                        uge_data['type_competence'] = 'PRODUCTION'
                    elif pd.notna(row.get('Distribution')) and str(row.get('Distribution')).lower() == 'oui':
                        uge_data['type_competence'] = 'DISTRIBUTION'

                    # Créer ou mettre à jour l'UGE
                    uge, created = UGE.objects.update_or_create(
                        code_sispea=code_sispea,
                        defaults=uge_data
                    )

                    if created:
                        stats['created'] += 1
                        self.stdout.write(f'  ✓ UGE créée: {nom_coll} (SISPEA: {code_sispea})')
                    else:
                        stats['updated'] += 1
                        self.stdout.write(f'  ✓ UGE mise à jour: {nom_coll} (SISPEA: {code_sispea})')

                    # Importer TOUS les indicateurs de performance
                    perf_result = self._import_performance_collectivite(uge, row, annee)
                    if perf_result == 'created':
                        stats['performances'] += 1
                    elif perf_result == 'updated':
                        stats['performances_updated'] += 1

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Erreur ligne {idx}: {str(e)}'))
                logger.error(f'Erreur import collectivité ligne {idx}: {str(e)}', exc_info=True)

        return stats

    def _import_performance_collectivite(self, uge, row, annee):
        """
        Importe TOUS les indicateurs de performance depuis la feuille Collectivités.

        Mapping complet des indicateurs selon le dictionnaire SISPEA.
        """
        try:
            perf_data = {
                'uge': uge,
                'annee': annee,
                'source_donnees': 'SISPEA'
            }

            # ===== INDICATEURS DESCRIPTIFS (D) =====

            # D101.0 = Estimation du nombre d'habitants desservis
            val = self._safe_int(row.get('D101.0'))
            if val:
                perf_data['population_desservie'] = val

            # D102.0 = Prix TTC du service au m³ pour 120 m³ (en €/m³)
            val = self._safe_decimal(row.get('D102.0'))
            if val:
                # D102.0 est déjà le prix pour 120m³
                perf_data['prix_eau_120m3_ttc'] = val * 120

            # D151.0 = Délai maximal d'ouverture des branchements (ignoré pour l'instant)

            # ===== INDICATEURS DE PERFORMANCE (P) =====

            # P101.1 = Taux de conformité microbiologie (%)
            val = self._safe_decimal(row.get('P101.1'))
            if val:
                perf_data['taux_conformite_bacterio'] = val

            # P102.1 = Taux de conformité physico-chimique (%)
            val = self._safe_decimal(row.get('P102.1'))
            if val:
                perf_data['taux_conformite_physico_chimique'] = val

            # P103.2B = Indice de connaissance et de gestion patrimoniale
            val = row.get('P103.2B')
            if pd.notna(val):
                perf_data['indice_connaissance_gestion'] = str(val)

            # P104.3 = Rendement du réseau de distribution (%)
            val = self._safe_decimal(row.get('P104.3'))
            if val:
                perf_data['rendement_reseau'] = val

            # P105.3 = Indice linéaire des volumes non comptés (m³/km/j)
            # Pas de champ direct dans le modèle, on pourrait le calculer

            # P106.3 = Indice linéaire de pertes en réseau (m³/km/j)
            val = self._safe_decimal(row.get('P106.3'))
            if val:
                perf_data['indice_lineaire_perte'] = val

            # P107.2 = Taux moyen de renouvellement des réseaux (%)
            val = self._safe_decimal(row.get('P107.2'))
            if val:
                perf_data['taux_renouvellement_reseau'] = val

            # P108.3 = Indice d'avancement de la protection de la ressource (%)
            val = self._safe_decimal(row.get('P108.3'))
            if val:
                perf_data['indice_protection_ressource'] = val

            # P109.0 = Montant des abandons de créance (€/m³) - converti en total via VP.119
            # On utilisera VP.119 qui est le montant total

            # P151.1 = Taux d'occurrence des interruptions (nb/1000ab)
            # Pas de champ direct, calculable depuis VP.020

            # P152.1 = Taux de respect du délai maximal d'ouverture (%)
            # Pas de champ dans le modèle actuel

            # P153.2 = Durée d'extinction de la dette (an)
            # Pas de champ dans le modèle actuel

            # P154.0 = Taux d'impayés (%)
            val = self._safe_decimal(row.get('P154.0'))
            if val:
                perf_data['taux_impaye'] = val

            # P155.1 = Taux de réclamations (nb/1000ab)
            # Calculable depuis VP.003 et VP.152

            # ===== VARIABLES DE PERFORMANCE (VP) =====

            # VP.056 = Nombre d'abonnés
            val = self._safe_int(row.get('VP.056'))
            if val:
                perf_data['nb_abonnes'] = val

            # VP.059 = Volume produit (m³)
            val = self._safe_int(row.get('VP.059'))
            if val:
                perf_data['volume_produit'] = val

            # VP.060 = Volume acheté (m³)
            val = self._safe_int(row.get('VP.060'))
            if val:
                perf_data['volume_achete'] = val

            # VP.061 = Volume vendu (m³)
            val = self._safe_int(row.get('VP.061'))
            if val:
                perf_data['volume_vendu'] = val

            # VP.062 = Volume prélevé (m³)
            # Pas de champ direct dans le modèle

            # VP.063 = Volume comptabilisé domestique (m³)
            val = self._safe_int(row.get('VP.063'))
            if val:
                perf_data['volume_consomme'] = val

            # VP.077 = Linéaire de réseau hors branchements (km)
            val = self._safe_decimal(row.get('VP.077'))
            if val:
                perf_data['lineaire_reseau_km'] = val

            # VP.119 = Somme des abandons de créances et versements (€ HTVA)
            # Pas de champ direct dans le modèle

            # VP.126 = Nombre de prélèvements microbiologiques
            val = self._safe_int(row.get('VP.126'))
            if val:
                perf_data['nb_prelevements_bacterio'] = val

            # VP.127 = Nombre de prélèvements microbiologiques non conformes
            # Utilisé pour calculer le taux de conformité

            # VP.128 = Nombre de prélèvements physico-chimiques
            val = self._safe_int(row.get('VP.128'))
            if val:
                perf_data['nb_prelevements_physico'] = val

            # VP.129 = Nombre de prélèvements physico-chimiques non conformes
            # Utilisé pour calculer le taux de conformité

            # VP.140 = Linéaire de réseau renouvelé sur 5 ans (km)
            # Pas de champ direct

            # VP.141 = Linéaire de réseau renouvelé dans l'année (km)
            val = self._safe_decimal(row.get('VP.141'))
            if val:
                perf_data['lineaire_renouvele_km'] = val

            # VP.182 = Encours total de la dette (€)
            # Pas de champ dans le modèle

            # VP.183 = Épargne brute annuelle (€)
            # Pas de champ dans le modèle

            # VP.185 = Montant TTC facturé au titre de l'année N-1 (€ TTC)
            # Pas de champ dans le modèle

            # VP.201 = Volume comptabilisé non domestique (m³)
            val = self._safe_int(row.get('VP.201'))
            if val:
                # On peut ajouter au volume comptabilisé si on le souhaite
                pass

            # VP.220 = Volume de l'entité de gestion (m³) = Volume mis en distribution
            val = self._safe_int(row.get('VP.220'))
            if val:
                perf_data['volume_mis_en_distribution'] = val

            # VP.221 = Volume consommé sans comptage (m³)
            # Pas de champ direct

            # VP.232 = Volumes consommés comptabilisés (m³)
            val = self._safe_int(row.get('VP.232'))
            if val and 'volume_consomme' not in perf_data:
                perf_data['volume_consomme'] = val

            # VP.268 = Montant restant impayés au 31/12/N (€ TTC)
            # Pas de champ dans le modèle

            # ===== DONNÉES DE CONTEXTE (DC) =====

            # DC.184 = Montant HT des recettes liées à la facturation (€ HT)
            # DC.192 = Nature des ressources (% eaux souterraines)
            # DC.195 = Montant financier HT des travaux engagés (€ HT)
            # DC.344 = Volume estimé de soutirage en cas d'incendie (m³)
            # → Pas de champs correspondants dans le modèle actuel

            # Calculer la complétude
            total_fields = 30  # Nombre de champs possibles dans UGEPerformanceAnnuelle
            filled_fields = sum(1 for k, v in perf_data.items()
                              if k not in ['uge', 'annee', 'source_donnees', 'completude'] and v is not None)
            if total_fields > 0:
                perf_data['completude'] = int((filled_fields / total_fields) * 100)

            # Créer ou mettre à jour la performance annuelle
            perf, created = UGEPerformanceAnnuelle.objects.update_or_create(
                uge=uge,
                annee=annee,
                defaults=perf_data
            )

            if created:
                self.stdout.write(f'    → Performance {annee} créée ({filled_fields} indicateurs renseignés)')
                return 'created'
            else:
                self.stdout.write(f'    → Performance {annee} mise à jour ({filled_fields} indicateurs renseignés)')
                return 'updated'

        except Exception as e:
            logger.error(f'Erreur import performance collectivité {uge.code_sispea}: {str(e)}', exc_info=True)
            return False

    def _import_entites_gestion(self, df_entites, annee, dry_run):
        """
        Importe les entités de gestion (UGE) et leurs performances.

        Cette feuille contient plus d'entités que Collectivités car elle inclut
        les syndicats intercommunaux et autres structures de gestion.
        """
        stats = {'created': 0, 'updated': 0, 'performances': 0, 'performances_updated': 0, 'errors': 0}

        for idx, row in df_entites.iterrows():
            try:
                # Extraction des données principales
                id_sispea_entite = row.get('Id SISPEA de l\'entité de gestion')
                code_uge = str(row.get('Code UGE de l\'entité de gestion', ''))
                nom_entite = str(row.get('Nom de l\'entité de gestion', ''))
                type_coll = str(row.get('Type collectivité', ''))

                if pd.isna(id_sispea_entite):
                    continue

                code_sispea = str(int(id_sispea_entite))

                # Données UGE complètes
                uge_data = {
                    'code_sispea': code_sispea,
                    'nom_uge': nom_entite if nom_entite and nom_entite != 'nan' else f'UGE {code_uge}',
                }

                # Code UGE
                if code_uge and code_uge != 'nan' and len(code_uge) > 0:
                    uge_data['code_uge'] = code_uge
                else:
                    uge_data['code_uge'] = code_sispea

                # Type UGE (déduit du type de collectivité)
                if type_coll and type_coll != 'nan':
                    if 'commune' in type_coll.lower():
                        uge_data['type_uge'] = 'Commune'
                    elif 'syndicat' in type_coll.lower():
                        uge_data['type_uge'] = 'Syndicat'
                    elif 'communauté' in type_coll.lower() or 'epci' in type_coll.lower():
                        uge_data['type_uge'] = 'EPCI'

                # Maître d'ouvrage (collectivité organisatrice)
                if pd.notna(row.get('Nom collectivité')):
                    uge_data['maitre_ouvrage'] = str(row.get('Nom collectivité'))

                # Compétences
                if pd.notna(row.get('Production')) and str(row.get('Production')).strip() == '1':
                    uge_data['type_competence'] = 'PRODUCTION'
                elif pd.notna(row.get('Distribution')) and str(row.get('Distribution')).strip() == '1':
                    uge_data['type_competence'] = 'DISTRIBUTION'

                # Mode de gestion et exploitant
                mode_gestion = row.get('Mode de gestion', '')
                if pd.notna(mode_gestion):
                    mode_str = str(mode_gestion).lower()
                    if 'régie' in mode_str or 'regie' in mode_str:
                        uge_data['type_mode_exploitation'] = 'REGIE'
                    elif 'délégation' in mode_str or 'dsp' in mode_str:
                        uge_data['type_mode_exploitation'] = 'DSP'
                    elif 'affermage' in mode_str:
                        uge_data['type_mode_exploitation'] = 'AFF_TERME'

                # Statut et nom de l'opérateur
                if pd.notna(row.get('Statut de l\'opérateur')):
                    statut_op = str(row.get('Statut de l\'opérateur'))
                    # Compléter le type de mode d'exploitation si besoin
                    if 'régie' in statut_op.lower() and 'type_mode_exploitation' not in uge_data:
                        uge_data['type_mode_exploitation'] = 'REGIE'
                    elif 'délégat' in statut_op.lower() and 'type_mode_exploitation' not in uge_data:
                        uge_data['type_mode_exploitation'] = 'DSP'

                if pd.notna(row.get('Nom de l\'opérateur')):
                    uge_data['exploitant'] = str(row.get('Nom de l\'opérateur'))

                # Date de fin de contrat (pas de champ date_debut dans le modèle)
                if pd.notna(row.get('Date de fin de contrat')):
                    try:
                        date_fin = pd.to_datetime(row.get('Date de fin de contrat'))
                        uge_data['date_fin_contrat_dsp'] = date_fin.date()
                    except:
                        pass

                # Informations géographiques (stockées dans des champs texte pour l'instant)
                # Agence de l'eau, Bassin, Sous-unité DCE
                # Ces informations pourraient être utilisées pour des analyses futures

                if dry_run:
                    self.stdout.write(f'  [DRY-RUN] Entité: {nom_entite} (SISPEA: {code_sispea}, Type: {type_coll})')
                    stats['created'] += 1
                    stats['performances'] += 1
                else:
                    # Créer ou mettre à jour l'UGE
                    uge, created = UGE.objects.update_or_create(
                        code_sispea=code_sispea,
                        defaults=uge_data
                    )

                    if created:
                        stats['created'] += 1
                        self.stdout.write(f'  ✓ UGE créée: {nom_entite} (SISPEA: {code_sispea})')
                    else:
                        stats['updated'] += 1
                        self.stdout.write(f'  ✓ UGE mise à jour: {nom_entite} (SISPEA: {code_sispea})')

                    # Importer les performances annuelles (même fonction que pour Collectivités)
                    perf_result = self._import_performance_collectivite(uge, row, annee)
                    if perf_result == 'created':
                        stats['performances'] += 1
                    elif perf_result == 'updated':
                        stats['performances_updated'] += 1

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Erreur ligne {idx}: {str(e)}'))
                logger.error(f'Erreur import entité de gestion ligne {idx}: {str(e)}', exc_info=True)

        return stats

    def _safe_decimal(self, value):
        """Convertit une valeur en Decimal de manière sécurisée."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def _safe_int(self, value):
        """Convertit une valeur en entier de manière sécurisée."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _import_performance_uge(self, uge, row, annee):
        """Importe les indicateurs de performance pour une UGE."""
        try:
            perf_data = {
                'uge': uge,
                'annee': annee,
                'source_donnees': 'SISPEA'
            }

            # Mapping des indicateurs SISPEA vers nos champs selon le dictionnaire fourni
            # D101.0 = Estimation du nombre d'habitants desservis
            # D102.0 = Prix TTC du service au m³ pour 120 m³
            # P101.1 = Taux conformité microbiologie (%)
            # P102.1 = Taux conformité physico-chimique (%)
            # P104.3 = Rendement du réseau de distribution (%)
            # P105.3 = Indice linéaire des volumes non comptés (m³/km/j)
            # P106.3 = Indice linéaire de pertes en réseau (m³/km/j)
            # P107.2 = Taux moyen de renouvellement des réseaux (%)
            # P108.3 = Indice d'avancement protection ressource (%)
            # VP.056 = Nombre d'abonnés
            # VP.059 = Volume produit (m³)
            # VP.060 = Volume acheté (m³)
            # VP.061 = Volume vendu (m³)
            # VP.062 = Volume prélevé (m³)
            # VP.063 = Volume comptabilisé domestique (m³)
            # VP.077 = Linéaire de réseau hors branchements (km)
            # VP.126/127 = Prélèvements microbiologie
            # VP.128/129 = Prélèvements physico-chimie
            # VP.140/141 = Linéaire réseau renouvelé

            # Population
            pop_desservie = self._safe_int(row.get('D101.0'))
            if pop_desservie:
                perf_data['population_desservie'] = pop_desservie

            # Population totale (depuis les données entité)
            pop_totale = self._safe_int(row.get('Pop de l\'entité de gestion sans double compte'))
            if pop_totale:
                perf_data['population_totale'] = pop_totale

            # Prix de l'eau
            prix_eau = self._safe_decimal(row.get('D102.0'))
            if prix_eau:
                # D102.0 est en €/m³, on calcule pour 120 m³
                perf_data['prix_eau_120m3_ttc'] = prix_eau * 120

            # Nombre d'abonnés
            nb_abonnes = self._safe_int(row.get('VP.056'))
            if nb_abonnes:
                perf_data['nb_abonnes'] = nb_abonnes

            # Volumes
            volume_produit = self._safe_int(row.get('VP.059'))
            if volume_produit:
                perf_data['volume_produit'] = volume_produit

            volume_achete = self._safe_int(row.get('VP.060'))
            if volume_achete:
                perf_data['volume_achete'] = volume_achete

            volume_vendu = self._safe_int(row.get('VP.061'))
            if volume_vendu:
                perf_data['volume_vendu'] = volume_vendu

            volume_comptabilise = self._safe_int(row.get('VP.063'))
            if volume_comptabilise:
                perf_data['volume_consomme'] = volume_comptabilise

            # Rendement et pertes
            rendement = self._safe_decimal(row.get('P104.3'))
            if rendement:
                perf_data['rendement_reseau'] = rendement

            ilp = self._safe_decimal(row.get('P106.3'))
            if ilp:
                perf_data['indice_lineaire_perte'] = ilp

            # Conformité
            conformite_bacterio = self._safe_decimal(row.get('P101.1'))
            if conformite_bacterio:
                perf_data['taux_conformite_bacterio'] = conformite_bacterio

            conformite_physico = self._safe_decimal(row.get('P102.1'))
            if conformite_physico:
                perf_data['taux_conformite_physico_chimique'] = conformite_physico

            # Nombre de prélèvements
            nb_prel_bacterio = self._safe_int(row.get('VP.126'))
            if nb_prel_bacterio:
                perf_data['nb_prelevements_bacterio'] = nb_prel_bacterio

            nb_prel_physico = self._safe_int(row.get('VP.128'))
            if nb_prel_physico:
                perf_data['nb_prelevements_physico'] = nb_prel_physico

            # Patrimoine
            lineaire_reseau = self._safe_decimal(row.get('VP.077'))
            if lineaire_reseau:
                perf_data['lineaire_reseau_km'] = lineaire_reseau

            lineaire_renouvele = self._safe_decimal(row.get('VP.141'))
            if lineaire_renouvele:
                perf_data['lineaire_renouvele_km'] = lineaire_renouvele

            taux_renouvellement = self._safe_decimal(row.get('P107.2'))
            if taux_renouvellement:
                perf_data['taux_renouvellement_reseau'] = taux_renouvellement

            # Protection de la ressource
            indice_protection = self._safe_decimal(row.get('P108.3'))
            if indice_protection:
                perf_data['indice_protection_ressource'] = indice_protection

            # Calculer la complétude (pourcentage de champs remplis)
            total_fields = len(perf_data) - 3  # Exclure uge, annee, source_donnees
            filled_fields = sum(1 for k, v in perf_data.items() if k not in ['uge', 'annee', 'source_donnees'] and v is not None)
            if total_fields > 0:
                perf_data['completude'] = int((filled_fields / total_fields) * 100)

            # Créer ou mettre à jour la performance annuelle
            perf, created = UGEPerformanceAnnuelle.objects.update_or_create(
                uge=uge,
                annee=annee,
                defaults=perf_data
            )

            if created:
                self.stdout.write(f'    → Performance {annee} créée ({filled_fields}/{total_fields} champs remplis)')
                return 'created'
            else:
                self.stdout.write(f'    → Performance {annee} mise à jour ({filled_fields}/{total_fields} champs remplis)')
                return 'updated'

        except Exception as e:
            logger.error(f'Erreur import performance UGE {uge.code_sispea}: {str(e)}')
            return None

    def _import_ouvrages(self, df_ouvrages, annee, dry_run):
        """Importe les ouvrages (captages)."""
        stats = {'created': 0, 'updated': 0, 'errors': 0}

        for idx, row in df_ouvrages.iterrows():
            try:
                # Extraction des données principales
                id_sispea_ouvrage = row.get('Id SISPEA ouvrage')
                nom_ouvrage = str(row.get('Nom ouvrage', ''))
                code_siseaux = str(row.get('Code SISEAUX ouvrage', ''))

                if pd.isna(id_sispea_ouvrage):
                    continue

                # Trouver l'UGE associée
                id_sispea_uge = row.get('Id SISPEA de l\'entité de gestion')
                uge = None
                if pd.notna(id_sispea_uge):
                    code_sispea_uge = str(int(id_sispea_uge))
                    try:
                        uge = UGE.objects.get(code_sispea=code_sispea_uge)
                    except UGE.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'  ⚠ UGE SISPEA {code_sispea_uge} non trouvée pour ouvrage {nom_ouvrage}'
                        ))

                if not dry_run:
                    # Chercher le captage par code SISE-EAUX
                    if code_siseaux and code_siseaux != 'nan' and len(code_siseaux) > 0:
                        try:
                            captage = Captage.objects.get(code_siseaux=code_siseaux)
                            # Mettre à jour l'UGE si trouvée
                            if uge and captage.uge != uge:
                                captage.uge = uge
                                captage.save()
                                self.stdout.write(f'  ✓ Captage mis à jour: {nom_ouvrage} ({code_siseaux})')
                            stats['updated'] += 1
                        except Captage.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f'  ⚠ Captage {code_siseaux} non trouvé. '
                                f'Créez d\'abord le captage avec sa géométrie.'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'  ⚠ Ouvrage {nom_ouvrage} sans code SISE-EAUX'
                        ))
                else:
                    self.stdout.write(f'  [DRY-RUN] Ouvrage: {nom_ouvrage} ({code_siseaux})')
                    stats['updated'] += 1

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Erreur ligne {idx}: {str(e)}'))
                logger.error(f'Erreur import ouvrage ligne {idx}: {str(e)}', exc_info=True)

        return stats

    def _afficher_resume(self, stats, dry_run):
        """Affiche le résumé de l'import."""
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RÉSUMÉ DE L\'IMPORT'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(f'Collectivités créées      : {stats["collectivites_created"]}')
        self.stdout.write(f'Collectivités MAJ         : {stats["collectivites_updated"]}')
        self.stdout.write(f'UGE créées                : {stats["uges_created"]}')
        self.stdout.write(f'UGE mises à jour          : {stats["uges_updated"]}')
        self.stdout.write(f'Ouvrages créés            : {stats["ouvrages_created"]}')
        self.stdout.write(f'Ouvrages MAJ              : {stats["ouvrages_updated"]}')
        self.stdout.write(f'Performances créées       : {stats["performances_created"]}')
        self.stdout.write(f'Performances mises à jour : {stats["performances_updated"]}')
        self.stdout.write(self.style.ERROR(f'Erreurs                   : {stats["errors"]}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\nMode DRY-RUN : Aucune donnée n\'a été enregistrée'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Import terminé avec succès'))
