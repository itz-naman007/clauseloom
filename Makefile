.PHONY: dev build test eval up down lint
dev:
	python scripts/dev.py
build:
	cd frontend && npm ci && npm run build
test:
	python -m pytest -q
	cd frontend && npm test
eval:
	python eval/run_eval.py
up:
	docker compose up --build -d
down:
	docker compose down
lint:
	python -m ruff check backend eval scripts
	cd frontend && npm run lint
