# PPTO API y dashboard

Servicio FastAPI para administrar y consultar registros de presupuesto (PPTO), incluyendo:

- CRUD con filtros por fechas y montos.
- Logs estructurados con `structlog`.
- Métricas Prometheus (latencia por endpoint y conteo de errores).
- Imagen Docker y `docker-compose` para staging.
- CI con lint (`ruff`, `black`) y pruebas (`pytest`).

## Ejecutar en local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La documentación OpenAPI está en `http://localhost:8000/docs` y el endpoint de salud en `/health`.

## Uso rápido

- **Crear/registrar intervención**:
  ```bash
  curl -X POST http://localhost:8000/entries/ \
    -H "Content-Type: application/json" \
    -d '{"fecha":"2025-01-05","win_tgm":1200,"coin_in":4800,"win_mesas":300,"drop_mesas":200,"nota":"Intervención de prueba"}'
  ```

- **Buscar con filtros** (rango de fechas y mínimo de coin-in):
  ```bash
  curl "http://localhost:8000/entries/?start_date=2025-01-01&end_date=2025-02-01&min_coin_in=3000"
  ```

## Métricas y logs

- Métricas Prometheus disponibles en `/metrics` (latencia `ppto_request_duration_seconds` y errores `ppto_request_errors_total`).
- Logs estructurados JSON a stdout; nivel configurable con `PPTO_LOG_LEVEL`.

## Docker y staging

Construir y correr localmente:

```bash
docker build -t ppto-api .
docker run -p 8000:8000 -e PPTO_DATABASE_URL=sqlite:///./data/ppto.db -v $(pwd)/data:/app/data ppto-api
```

Staging con `docker-compose`:

```bash
docker compose -f docker-compose.staging.yml up --build
```

## CI y calidad

La canalización (`.github/workflows/ci.yml`) ejecuta:

- `ruff check app tests`
- `black --check app tests`
- `pytest`

Puedes ejecutarlos manualmente:

```bash
ruff check app tests
black --check app tests
pytest
```
