.PHONY: help setup test lint format check pre-commit up down migrate createsuperuser shell worker clean coverage

setup:
	uv sync

test:
	export USE_SQLITE_FOR_TESTS=1 && \
	export RABBITMQ_URL="amqp://guest:guest@localhost:5672/" && \
	export REDIS_URL="redis://localhost:6379/0" && \
	export DJANGO_SETTINGS_MODULE="olki_backend.settings" && \
	pytest --cov=. --cov-report=term-missing --cov-report=html -v

coverage:
	export USE_SQLITE_FOR_TESTS=1 && \
	export RABBITMQ_URL="amqp://guest:guest@localhost:5672/" && \
	export REDIS_URL="redis://localhost:6379/0" && \
	export DJANGO_SETTINGS_MODULE="olki_backend.settings" && \
	pytest --cov=. --cov-report=html && \
	open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Откройте htmlcov/index.html в браузере"

lint:
	ruff check .

format:
	ruff format .

check: lint
	ruff check . --fix
	ruff format .

pre-commit:
	pre-commit run --all-files

pre-commit-install:
	pre-commit install

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec web python manage.py migrate

migrate-local:
	export DATABASE_URL="postgresql://olki_user:olki_password@localhost:5432/olki_db" && \
	export RABBITMQ_URL="amqp://olki_user:olki_password@localhost:5672/" && \
	export REDIS_URL="redis://localhost:6379/0" && \
	export DJANGO_SETTINGS_MODULE="olki_backend.settings" && \
	python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

makemigrations-local:
	export DATABASE_URL="postgresql://olki_user:olki_password@localhost:5432/olki_db" && \
	export RABBITMQ_URL="amqp://olki_user:olki_password@localhost:5672/" && \
	export REDIS_URL="redis://localhost:6379/0" && \
	export DJANGO_SETTINGS_MODULE="olki_backend.settings" && \
	python manage.py makemigrations

worker:
	export DATABASE_URL="postgresql://olki_user:olki_password@localhost:5432/olki_db" && \
	export RABBITMQ_URL="amqp://olki_user:olki_password@localhost:5672/" && \
	export REDIS_URL="redis://localhost:6379/0" && \
	export DJANGO_SETTINGS_MODULE="olki_backend.settings" && \
	python manage.py runworker

createsuperuser:
	docker compose exec web python manage.py createsuperuser

runserver:
	export DATABASE_URL="postgresql://olki_user:olki_password@localhost:5432/olki_db" && \
	export RABBITMQ_URL="amqp://olki_user:olki_password@localhost:5672/" && \
	export REDIS_URL="redis://localhost:6379/0" && \
	export DJANGO_SETTINGS_MODULE="olki_backend.settings" && \
	python manage.py runserver

clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .ruff_cache

clean-docker:
	docker compose down -v
	docker system prune -f

all: clean setup check test ## Выполнить все проверки (clean, install, check, test)

test-e2e: ## Запустить end-to-end тесты
	python3 test_e2e.py

.PHONY: test-e2e
