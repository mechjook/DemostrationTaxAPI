# API de Validación Tributaria — Chile

Microservicio REST para validación y cálculo tributario chileno. Incluye validación de RUT, cálculo de IVA, retención de honorarios, topes imponibles/cotizaciones y simulador de F29. Con Swagger UI, Dockerfile y demo interactiva en GitHub Pages.

[![Tax API Pipeline](https://github.com/mechjook/DemostrationTaxAPI/actions/workflows/tax_api_pipeline.yml/badge.svg)](https://github.com/mechjook/DemostrationTaxAPI/actions/workflows/tax_api_pipeline.yml)

## Demo

Disponible en: **[GitHub Pages](https://mechjook.github.io/DemostrationTaxAPI/)**

## Arquitectura

```
┌────────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  FastAPI + Swagger  │───▶│  Lógica          │───▶│  Modelos         │
│  11 endpoints REST  │    │  Tributaria      │    │  Pydantic        │
└────────────────────┘    └──────────────────┘    └──────────────────┘
         │
         ▼
┌────────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Demo HTML         │    │  Dockerfile       │    │  Tests           │
│  GitHub Pages      │    │  Containerización │    │  pytest + httpx  │
└────────────────────┘    └──────────────────┘    └──────────────────┘
```

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/rut/validar` | Validar RUT chileno (dígito verificador módulo 11) |
| POST | `/api/iva/desde-neto` | Calcular IVA y bruto desde monto neto |
| POST | `/api/iva/desde-bruto` | Extraer neto e IVA desde monto bruto |
| POST | `/api/iva/factura` | Desglose completo de factura con items |
| POST | `/api/honorarios/retencion` | Calcular retención desde monto bruto |
| POST | `/api/honorarios/liquido` | Calcular bruto necesario desde líquido |
| POST | `/api/honorarios/anual` | Simulación anual de honorarios |
| POST | `/api/topes/calcular` | Topes imponibles en pesos según UF |
| POST | `/api/topes/cotizaciones` | Cotizaciones previsionales completas |
| GET | `/api/topes/afps` | Listar AFPs con tasas |
| POST | `/api/f29/simular` | Simulador de declaración F29 |

## Dominios Tributarios

| Dominio | Descripción |
|---------|-------------|
| **RUT** | Validación con algoritmo módulo 11, formateo, detección de errores |
| **IVA** | Tasa 19%, cálculo neto↔bruto, desglose de facturas |
| **Honorarios** | Retención 2024-2027 (13.75%→17%), cálculo inverso, simulación anual |
| **Topes** | AFP (90 UF), salud (7%), AFC, SIS. 7 AFPs con tasas actualizadas |
| **F29** | Débito/crédito fiscal, remanente, PPM (1%), retenciones |

## Ejecución Local

```bash
pip install -r requirements.txt

# Ejecutar API
uvicorn src.api:app --reload

# Swagger UI
open http://localhost:8000/docs
```

## Docker

```bash
docker build -t tax-api .
docker run -p 8000:8000 tax-api
```

## Tests

```bash
pytest tests/ -v
```

## CI/CD

El workflow de GitHub Actions ejecuta:
1. **Tests** — pytest con tests unitarios + integración de endpoints
2. **Deploy** — publica la demo interactiva en GitHub Pages (solo en `main`)

## Stack

- Python 3.12
- FastAPI / Pydantic
- pytest / httpx
- Docker
- GitHub Actions + GitHub Pages

## Autor

**José Nicolás Candia** — [@mechjook](https://github.com/mechjook)
