.PHONY: api-dev web-dev docker-up docker-down lint test-api test-web format migrate

api-dev:
	uvicorn services.api.app.main:app --reload

web-dev:
	cd apps/web && npm run dev

docker-up:
	cd infra/docker && docker compose up --build

docker-down:
	cd infra/docker && docker compose down

lint:
	cd apps/web && npm run lint

test-api:
	pytest services/api/tests

test-web:
	cd apps/web && npm run test

format:
	cd apps/web && npm run lint -- --fix

migrate:
	cd services/api && alembic upgrade head
