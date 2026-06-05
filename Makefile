.PHONY: up down logs test lint dev

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f

test:
	pytest tests/ -v --cov=api --cov-fail-under=75

lint:
	flake8 api/ dashboard/ tests/ --max-line-length=100

dev:
	@echo "Starting API..."
	uvicorn api.main:app --reload --port 8000 &
	@echo "Starting Dashboard..."
	streamlit run dashboard/app.py
