# DevOps Monitoring Dashboard

A real-time DevOps monitoring dashboard with a FastAPI backend and a Streamlit frontend.

## Project Structure

```
mini-projet-python/
├── api/
│   ├── main.py       # FastAPI app (endpoints + WebSocket)
│   ├── models.py     # Server dataclass + Pydantic schemas
│   ├── auth.py       # API key authentication
│   ├── metrics.py    # System metrics via psutil
│   └── poller.py     # Async background health checker
├── dashboard/
│   └── app.py        # Streamlit frontend
├── tests/
│   ├── test_metrics.py
│   └── test_routes.py
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/Hyvernat/mini-projet-python.git
cd mini-projet-python

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Run

**Backend (FastAPI):**
```bash
uvicorn api.main:app --reload --port 8000
```
Swagger UI: http://localhost:8000/docs

**Frontend (Streamlit):**
```bash
streamlit run dashboard/app.py
```
Dashboard: http://localhost:8501

## API Key

Default API key for local dev: `dev-secret-key`

Override with environment variable:
```bash
API_KEY=your-secret uvicorn api.main:app --reload --port 8000
```

Protected endpoints (require `X-API-Key` header):
- `POST /servers`
- `DELETE /servers/{id}`

## Tests

```bash
pytest tests/ -v
pytest tests/ --cov=api --cov-report=term-missing
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | public | API health check |
| GET | `/metrics` | public | System metrics snapshot |
| WS | `/ws/metrics` | public | Live metrics stream (1s interval) |
| POST | `/servers` | API key | Register a server |
| GET | `/servers` | public | List servers (optional `?status=UP`) |
| GET | `/servers/{id}` | public | Get one server |
| DELETE | `/servers/{id}` | API key | Remove a server |
| POST | `/servers/{id}/check` | public | Trigger immediate health check |
