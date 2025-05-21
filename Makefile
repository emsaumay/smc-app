.PHONY: help build up down logs shell test clean migrate collectstatic

# Default environment
ENV ?= dev

help: ## Show this help message
	@echo 'Usage: make [target] [ENV=dev|prod]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial setup - copy environment file
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env file with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

build: ## Build Docker images
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml build; \
	else \
		docker-compose build; \
	fi

up: ## Start services
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml up -d; \
	else \
		docker-compose up -d; \
	fi

down: ## Stop services
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml down; \
	else \
		docker-compose down; \
	fi

logs: ## View logs
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml logs -f; \
	else \
		docker-compose logs -f; \
	fi

shell: ## Open Django shell
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml exec web python manage.py shell; \
	else \
		docker-compose exec web python manage.py shell; \
	fi

bash: ## Open bash shell in web container
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml exec web bash; \
	else \
		docker-compose exec web bash; \
	fi

migrate: ## Run database migrations
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml exec web python manage.py migrate; \
	else \
		docker-compose exec web python manage.py migrate; \
	fi

collectstatic: ## Collect static files
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput; \
	else \
		docker-compose exec web python manage.py collectstatic --noinput; \
	fi

createsuperuser: ## Create Django superuser
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser; \
	else \
		docker-compose exec web python manage.py createsuperuser; \
	fi

test: ## Run tests
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml exec web python manage.py test; \
	else \
		docker-compose exec web python manage.py test; \
	fi

clean: ## Clean up Docker resources
	docker-compose down -v --remove-orphans
	docker system prune -f

restart: down up ## Restart services

status: ## Show service status
	@if [ "$(ENV)" = "prod" ]; then \
		docker-compose -f docker-compose.prod.yml ps; \
	else \
		docker-compose ps; \
	fi

# Development shortcuts
dev-up: ## Start development environment
	make up ENV=dev

dev-logs: ## View development logs
	make logs ENV=dev

dev-shell: ## Open shell in development
	make shell ENV=dev

# Production shortcuts
prod-up: ## Start production environment
	make up ENV=prod

prod-logs: ## View production logs
	make logs ENV=prod

prod-shell: ## Open shell in production
	make shell ENV=prod