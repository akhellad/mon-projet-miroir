.PHONY: help build up down restart logs logs-db logs-backend logs-frontend clean migrate makemigrations shell db-shell test createsuperuser collectstatic status rebuild

help:
	@echo "Commandes disponibles pour le projet SDAEP Observatoire:"
	@echo ""
	@echo "  make build          - Construire les images Docker"
	@echo "  make up             - Démarrer tous les services"
	@echo "  make down           - Arrêter tous les services"
	@echo "  make restart        - Redémarrer tous les services"
	@echo "  make logs           - Afficher les logs de tous les services"
	@echo "  make logs-db        - Afficher les logs de la base de données"
	@echo "  make logs-backend   - Afficher les logs du backend"
	@echo "  make logs-frontend  - Afficher les logs du frontend"
	@echo "  make clean          - Nettoyer les containers et volumes"
	@echo "  make migrate        - Exécuter les migrations Django"
	@echo "  make makemigrations - Créer les migrations Django"
	@echo "  make shell          - Ouvrir un shell dans le container backend"
	@echo "  make db-shell       - Ouvrir un shell PostgreSQL"
	@echo "  make test           - Lancer les tests"
	@echo "  make createsuperuser - Créer un superuser Django"
	@echo "  make status         - Vérifier l'état des services"
	@echo "  make rebuild        - Reconstruire et redémarrer"

# Docker - Build
build:
	docker compose build

# Docker - Démarrage
up:
	docker compose up -d

# Docker - Arrêt
down:
	docker compose down

# Docker - Redémarrage
restart:
	docker compose restart

# Logs - Tous les services
logs:
	docker compose logs -f

# Logs - Base de données
logs-db:
	docker compose logs -f db

# Logs - Backend
logs-backend:
	docker compose logs -f backend

# Logs - Frontend
logs-frontend:
	docker compose logs -f frontend

# Nettoyage complet
clean:
	docker compose down -v
	@echo "Containers et volumes supprimés"

# Django - Migrations
migrate:
	docker compose exec backend python manage.py migrate

# Django - Créer des migrations
makemigrations:
	docker compose exec backend python manage.py makemigrations

# Shell Django
shell:
	docker compose exec backend python manage.py shell

# Shell PostgreSQL
db-shell:
	docker compose exec db psql -U $${DB_USER} -d $${DB_NAME}

# Tests
test:
	docker compose exec backend python manage.py test

# Créer un superuser Django
createsuperuser:
	docker compose exec backend python manage.py createsuperuser

# Collecter les fichiers statiques
collectstatic:
	docker compose exec backend python manage.py collectstatic --no-input

# Vérifier l'état des services
status:
	docker compose ps

# Reconstruire et redémarrer
rebuild:
	docker compose down
	docker compose build
	docker compose up -d
