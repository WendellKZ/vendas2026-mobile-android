.PHONY: up down logs test lint format seed

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

test:
	docker compose run --rm api pytest -q

lint:
	docker compose run --rm api python -m compileall app

format:
	@echo "Projeto preparado para formatter externo; mantendo sem alteração automática."

seed:
	docker compose run --rm api python scripts/seed.py
