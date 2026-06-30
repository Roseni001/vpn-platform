# vpn-platform backend

Backend foundation for `vpn-platform`.

## Stack

- Python 3.12+
- FastAPI
- uvicorn
- httpx
- python-dotenv
- pydantic-settings

## Architecture

The API is provider-agnostic. Endpoints do not know about WG-Easy and work through application services and interfaces.

```text
app/
  api/          HTTP routes and FastAPI dependencies
  core/         config, logging, error handling, provider composition
  interfaces/   provider contracts
  providers/    concrete external provider implementations
  services/     application services
```

## Included

- Environment-based configuration
- Clean logging
- Centralized API error handling
- `VPNProvider` interface
- `WGEasyProvider` implementation
- Health endpoint
- VPN client management endpoints

Database, application authentication, and Docker are intentionally not included.

## Setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

OpenAPI docs are available at `/docs`.

## Endpoints

- `GET /health`
- `GET /clients`
- `GET /clients/{client_id}`
- `POST /clients`
- `DELETE /clients/{client_id}`
- `GET /clients/{client_id}/configuration`
