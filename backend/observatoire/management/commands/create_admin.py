"""
Commande de management Django pour créer un utilisateur administrateur.

Usage:
    python manage.py create_admin
    python manage.py create_admin --username admin --password mypassword
    python manage.py create_admin --force  # Remplace l'utilisateur s'il existe déjà
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Créer un utilisateur administrateur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Nom d\'utilisateur (défaut: admin)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin',
            help='Mot de passe (défaut: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email (défaut: admin@example.com)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Remplacer l\'utilisateur s\'il existe déjà'
        )

    def handle(self, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        force = options['force']

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('  Création d\'un utilisateur administrateur'))
        self.stdout.write('=' * 60)
        self.stdout.write('')

        # Vérifier si l'utilisateur existe déjà
        user_exists = User.objects.filter(username=username).exists()

        if user_exists and not force:
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.WARNING(f" L'utilisateur '{username}' existe déjà.")
            )
            self.stdout.write(f"   - ID: {user.id}")
            self.stdout.write(f"   - Email: {user.email}")
            self.stdout.write(f"   - Rôle: {user.get_role_display()}")
            self.stdout.write(f"   - Actif: {'Oui' if user.is_active else 'Non'}")
            self.stdout.write(f"   - Date de création: {user.date_joined}")
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    "Utilisez --force pour remplacer l'utilisateur existant"
                )
            )
            return

        # Si force et utilisateur existe, le supprimer d'abord
        if user_exists and force:
            User.objects.filter(username=username).delete()
            self.stdout.write(
                self.style.WARNING(f"Utilisateur existant '{username}' supprimé")
            )

        # Créer l'utilisateur
        user = User.objects.create(
            username=username,
            email=email,
            role='admin',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        user.set_password(password)
        user.save()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Utilisateur administrateur créé avec succès!'))
        self.stdout.write(f"   - Username: {username}")
        self.stdout.write(f"   - Email: {email}")
        self.stdout.write(f"   - Password: {password}")
        self.stdout.write(f"   - Rôle: Administrateur")
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                "IMPORTANT: Changez le mot de passe après la première connexion!"
            )
        )
        self.stdout.write('')
        self.stdout.write('=' * 60)
