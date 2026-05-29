.PHONY: setup run test lint docker-build docker-up docker-down

setup:
	uv venv
	uv pip install -e .[dev]

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

test:
	pytest tests/

lint:
	ruff check app/

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
