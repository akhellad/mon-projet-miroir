from django.core.management.base import BaseCommand
from django.db import transaction
from observatoire.models import Layer, Feature, UDI, Commune
import requests
from collections import defaultdict
from datetime import datetime
from django.db import models


class Command(BaseCommand):
    help = 'Importe les UDI de l\'Ardèche depuis l\'API Hub\'eau'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Supprimer la couche UDI existante avant l\'import',
        )

    def get_ardeche_communes(self):
        codes = list(Commune.objects.filter(
            code_insee__startswith='07'
        ).values_list('code_insee', flat=True))
        self.stdout.write(f'🎯 {len(codes)} communes trouvées en base')
        return codes

    def fetch_udi_data(self, communes_codes):
        base_url = 'https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/communes_udi'
        all_data = []
        batch_size = 20
        
        for i in range(0, len(communes_codes), batch_size):
            batch = communes_codes[i:i+batch_size]
            codes = ','.join(batch)
            page = 1
            
            while True:
                url = f'{base_url}?code_commune={codes}&page={page}&size=5000'
                self.stdout.write(f'Batch {i//batch_size + 1}/{(len(communes_codes)-1)//batch_size + 1}, page {page}...')
                
                try:
                    r = requests.get(url, timeout=30)
                    r.raise_for_status()
                    json_data = r.json()
                    
                    data = json_data.get('data', [])
                    if not data:
                        break
                    
                    all_data.extend(data)
                    
                    if not json_data.get('next'):
                        break
                    page += 1
                    
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f'Erreur API: {e}'))
                    break
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(all_data)} enregistrements récupérés'))
        return all_data

    def parse_date(self, date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Début de l\'import des UDI de l\'Ardèche...'))

        existing_layer = Layer.objects.filter(name='UDI').first()

        if existing_layer:
            if options['force']:
                self.stdout.write(self.style.WARNING('Suppression de la couche existante...'))
                existing_layer.delete()
            else:
                self.stdout.write(self.style.ERROR(
                    'Une couche "UDI" existe déjà. Utilisez --force pour la remplacer.'
                ))
                return

        layer = Layer.objects.create(
            name='UDI',
            description='Unités de Distribution d\'Eau en Ardèche',
            geometry_type='Point',
            identifier_field='code_ins_udi',
            style_color='#3388ff',
            style_weight=2,
            style_opacity=0.8,
            style_fill_opacity=0.5,
            source_file='hubeau.eaufrance.fr',
            srid=2154,
            visible=True
        )

        self.stdout.write(self.style.SUCCESS(f'Couche "{layer.name}" créée'))

        communes_codes = self.get_ardeche_communes()
        raw_data = self.fetch_udi_data(communes_codes)

        udi_data = defaultdict(lambda: {
            'communes': set(),
            'quartiers': set(),
            'nom': None,
            'debut_alim': None
        })

        for record in raw_data:
            code_reseau = record.get('code_reseau')
            code_commune = record.get('code_commune')
            nom_reseau = record.get('nom_reseau')
            nom_quartier = record.get('nom_quartier')
            debut_alim = record.get('debut_alim')
            
            if not code_reseau or not code_commune:
                continue
            
            udi_data[code_reseau]['communes'].add(code_commune)
            udi_data[code_reseau]['nom'] = nom_reseau
            if nom_quartier and nom_quartier != '-':
                udi_data[code_reseau]['quartiers'].add(nom_quartier)
            if debut_alim and not udi_data[code_reseau]['debut_alim']:
                udi_data[code_reseau]['debut_alim'] = debut_alim

        self.stdout.write(f'📊 {len(udi_data)} UDI uniques identifiées')

        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for code_reseau, data in udi_data.items():
                communes_obj = Commune.objects.filter(code_insee__in=data['communes'])
                
                if not communes_obj.exists():
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  UDI {code_reseau} ignorée: communes introuvables'
                    ))
                    skipped_count += 1
                    continue

                udi = UDI.objects.create(
                    code_ins_udi=code_reseau,
                    nom_ins_udi=data['nom'] or f'UDI {code_reseau}',
                    nom_quartier=', '.join(data['quartiers']) if data['quartiers'] else None,
                    date_debut_validite_udi=self.parse_date(data['debut_alim']),
                    type_usage_direct='AEP',
                    type_etat_activite_ins='ACTIF',
                    type_nature_eau='EAU_DISTRIBUTEE'
                )

                udi.communes.set(communes_obj)
                
                created_count += 1
                
                if created_count % 50 == 0:
                    self.stdout.write(f'  ... {created_count} UDI importées')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Import terminé'))
        self.stdout.write(self.style.SUCCESS(f'{created_count} UDI importées'))
        self.stdout.write(self.style.WARNING(f'{skipped_count} UDI ignorées'))
        
        multi_communes = UDI.objects.annotate(
            nb_communes=models.Count('communes')
        ).filter(nb_communes__gt=1).count()
        
        self.stdout.write(f'📍 {multi_communes} UDI multi-communes')