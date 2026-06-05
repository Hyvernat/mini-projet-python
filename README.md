# DevOps Monitoring Dashboard

Real-time DevOps monitoring dashboard — FastAPI backend + Streamlit frontend, containerised with Docker, deployed on Azure via GitHub Actions CI/CD.

## Architecture

```
GitHub Actions CI/CD
  ├── lint (flake8)
  ├── test (pytest --cov ≥ 75%)
  ├── build & push → Azure Container Registry
  └── deploy → Azure Container Apps
         │
         ├── devops-monitor-api   (FastAPI — port 8000)
         └── devops-monitor-dashboard  (Streamlit — port 8501)
```

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Make

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Hyvernat/mini-projet-python.git
cd mini-projet-python

# 2. Configure environment
cp .env.example .env   # fill in API_KEY

# 3. Start the full stack
make up

# 4. Run tests
make test
```

- API Swagger UI: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## Local Dev (without Docker)

```bash
pip install -r requirements.txt
make dev
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make up` | Start full stack with Docker Compose |
| `make down` | Stop and remove containers |
| `make logs` | Follow container logs |
| `make test` | Run pytest with coverage ≥ 75% |
| `make lint` | Run flake8 linter |
| `make dev` | Start API + Dashboard locally |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | public | Health check |
| GET | `/metrics` | public | CPU, Memory, Disk snapshot |
| WS | `/ws/metrics` | public | Live metrics stream (1s) |
| POST | `/servers` | API key | Register a server |
| GET | `/servers` | public | List servers |
| GET | `/servers/{id}` | public | Get one server |
| DELETE | `/servers/{id}` | API key | Remove a server |
| POST | `/servers/{id}/check` | public | Trigger health check |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | `dev-secret-key` |
| `API_BASE_URL` | API URL seen by dashboard | `http://api:8000` |

## GitHub Secrets (for CI/CD)

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | Azure App Registration client ID |
| `AZURE_CLIENT_SECRET` | Azure App Registration secret |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `ACR_NAME` | Azure Container Registry name |
| `API_KEY` | API key injected in Container Apps |

## Project Structure

```
mini-projet-python/
├── api/
│   ├── main.py       # FastAPI app + WebSocket + lifespan
│   ├── models.py     # Server dataclass + Pydantic schemas
│   ├── auth.py       # API key authentication
│   ├── metrics.py    # System metrics (psutil)
│   ├── poller.py     # Async background health checker
│   └── Dockerfile    # Multi-stage build
├── dashboard/
│   ├── app.py        # Streamlit frontend (2 tabs)
│   └── Dockerfile
├── tests/
│   ├── test_metrics.py
│   └── test_routes.py
├── .github/workflows/ci-cd.yml
├── docker-compose.yml
├── Makefile
├── .env.example
├── .dockerignore
├── requirements.txt
└── README.md
```
