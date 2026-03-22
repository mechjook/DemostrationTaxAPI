"""
API REST — FastAPI con endpoints de validación y cálculo tributario.

Endpoints:
  POST /api/rut/validar           — Validar un RUT chileno
  POST /api/iva/desde-neto        — Calcular IVA desde monto neto
  POST /api/iva/desde-bruto       — Calcular neto desde monto bruto
  POST /api/iva/factura           — Desglose de factura con items
  POST /api/honorarios/retencion  — Calcular retención de honorarios
  POST /api/honorarios/liquido    — Calcular bruto desde líquido deseado
  POST /api/honorarios/anual      — Simulación anual de honorarios
  POST /api/topes/calcular        — Calcular topes imponibles
  POST /api/topes/cotizaciones    — Calcular cotizaciones previsionales
  GET  /api/topes/afps            — Listar AFPs y tasas
  POST /api/f29/simular           — Simular declaración F29

Swagger UI disponible en /docs
Redoc disponible en /redoc

Autor: José Nicolás Candia (@mechjook)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.rut import validar_rut
from src.iva import calcular_iva_desde_neto, calcular_neto_desde_bruto, desglose_factura
from src.honorarios import (
    calcular_retencion_desde_bruto,
    calcular_bruto_desde_liquido,
    simular_honorarios_anuales,
)
from src.topes import calcular_topes, calcular_cotizaciones, listar_afps
from src.f29 import simular_f29


# --- App ---
app = FastAPI(
    title="API de Validación Tributaria — Chile",
    description=(
        "Microservicio REST para validación y cálculo tributario chileno. "
        "Incluye validación de RUT, cálculo de IVA, retención de honorarios, "
        "topes imponibles/cotizaciones y simulador de F29."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Modelos Pydantic ---

class RutRequest(BaseModel):
    rut: str = Field(..., examples=["12.345.678-5"], description="RUT a validar")

class MontoNetoRequest(BaseModel):
    monto_neto: float = Field(..., gt=0, examples=[1000000], description="Monto neto (sin IVA)")
    tasa: float = Field(default=0.19, ge=0, le=1, description="Tasa de IVA")

class MontoBrutoRequest(BaseModel):
    monto_bruto: float = Field(..., gt=0, examples=[1190000], description="Monto bruto (con IVA)")
    tasa: float = Field(default=0.19, ge=0, le=1, description="Tasa de IVA")

class FacturaItem(BaseModel):
    descripcion: str = Field(..., examples=["Servicio consultoría"])
    cantidad: int = Field(..., gt=0, examples=[1])
    precio_unitario_neto: float = Field(..., gt=0, examples=[500000])

class FacturaRequest(BaseModel):
    items: list[FacturaItem] = Field(..., min_length=1)

class HonorariosBrutoRequest(BaseModel):
    monto_bruto: float = Field(..., gt=0, examples=[1000000], description="Monto bruto de la boleta")
    anio: int = Field(default=2026, ge=2020, le=2030, description="Año tributario")

class HonorariosLiquidoRequest(BaseModel):
    monto_liquido: float = Field(..., gt=0, examples=[847500], description="Monto líquido deseado")
    anio: int = Field(default=2026, ge=2020, le=2030, description="Año tributario")

class HonorariosAnualRequest(BaseModel):
    monto_mensual_bruto: float = Field(..., gt=0, examples=[1500000])
    meses: int = Field(default=12, ge=1, le=12)
    anio: int = Field(default=2026, ge=2020, le=2030)

class TopesRequest(BaseModel):
    valor_uf: float = Field(default=39842.0, gt=0, description="Valor de la UF en pesos")

class CotizacionesRequest(BaseModel):
    renta_bruta: float = Field(..., gt=0, examples=[1500000], description="Renta bruta mensual")
    afp: str = Field(default="Habitat", examples=["Habitat"], description="Nombre de la AFP")
    tipo_contrato: str = Field(default="indefinido", pattern="^(indefinido|plazo_fijo)$")
    valor_uf: float = Field(default=39842.0, gt=0)

class F29Request(BaseModel):
    ventas_netas: float = Field(..., ge=0, examples=[10000000])
    compras_netas: float = Field(..., ge=0, examples=[6000000])
    ventas_exentas: float = Field(default=0, ge=0)
    compras_activo_fijo: float = Field(default=0, ge=0)
    remanente_anterior: float = Field(default=0, ge=0)
    tasa_ppm: float = Field(default=0.01, ge=0, le=0.1)
    retenciones_honorarios: float = Field(default=0, ge=0)


# --- Endpoints RUT ---

@app.post("/api/rut/validar", tags=["RUT"])
def api_validar_rut(req: RutRequest):
    """Valida un RUT chileno y retorna su formato correcto."""
    return validar_rut(req.rut)


# --- Endpoints IVA ---

@app.post("/api/iva/desde-neto", tags=["IVA"])
def api_iva_desde_neto(req: MontoNetoRequest):
    """Calcula IVA y monto bruto desde un monto neto."""
    try:
        return calcular_iva_desde_neto(req.monto_neto, req.tasa)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/iva/desde-bruto", tags=["IVA"])
def api_iva_desde_bruto(req: MontoBrutoRequest):
    """Calcula monto neto e IVA desde un monto bruto (IVA incluido)."""
    try:
        return calcular_neto_desde_bruto(req.monto_bruto, req.tasa)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/iva/factura", tags=["IVA"])
def api_desglose_factura(req: FacturaRequest):
    """Genera desglose completo de una factura con múltiples items."""
    try:
        items = [item.model_dump() for item in req.items]
        return desglose_factura(items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Endpoints Honorarios ---

@app.post("/api/honorarios/retencion", tags=["Honorarios"])
def api_retencion_honorarios(req: HonorariosBrutoRequest):
    """Calcula retención y líquido desde monto bruto de boleta."""
    try:
        return calcular_retencion_desde_bruto(req.monto_bruto, req.anio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/honorarios/liquido", tags=["Honorarios"])
def api_bruto_desde_liquido(req: HonorariosLiquidoRequest):
    """Calcula monto bruto necesario para recibir un líquido deseado."""
    try:
        return calcular_bruto_desde_liquido(req.monto_liquido, req.anio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/honorarios/anual", tags=["Honorarios"])
def api_honorarios_anuales(req: HonorariosAnualRequest):
    """Simula honorarios anuales con retenciones acumuladas."""
    try:
        return simular_honorarios_anuales(req.monto_mensual_bruto, req.meses, req.anio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Endpoints Topes ---

@app.post("/api/topes/calcular", tags=["Topes Imponibles"])
def api_calcular_topes(req: TopesRequest):
    """Calcula topes imponibles en pesos según valor de UF."""
    return calcular_topes(req.valor_uf)


@app.post("/api/topes/cotizaciones", tags=["Topes Imponibles"])
def api_calcular_cotizaciones(req: CotizacionesRequest):
    """Calcula cotizaciones previsionales completas de un trabajador."""
    try:
        return calcular_cotizaciones(req.renta_bruta, req.afp, req.tipo_contrato, req.valor_uf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/topes/afps", tags=["Topes Imponibles"])
def api_listar_afps():
    """Lista todas las AFPs con sus tasas de cotización."""
    return listar_afps()


# --- Endpoints F29 ---

@app.post("/api/f29/simular", tags=["F29"])
def api_simular_f29(req: F29Request):
    """Simula la declaración mensual del Formulario 29 (IVA + PPM)."""
    try:
        return simular_f29(
            ventas_netas=req.ventas_netas,
            compras_netas=req.compras_netas,
            ventas_exentas=req.ventas_exentas,
            compras_activo_fijo=req.compras_activo_fijo,
            remanente_anterior=req.remanente_anterior,
            tasa_ppm=req.tasa_ppm,
            retenciones_honorarios=req.retenciones_honorarios,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Health ---

@app.get("/api/health", tags=["Sistema"])
def health():
    """Health check del servicio."""
    return {"status": "ok", "service": "tax-api", "version": "1.0.0"}
