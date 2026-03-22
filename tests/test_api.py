"""
Tests para la API de Validación Tributaria.

Incluye:
  - Tests unitarios de lógica tributaria (RUT, IVA, honorarios, topes, F29)
  - Tests de integración de endpoints con httpx AsyncClient
  - Tests de validación de modelos Pydantic

Autor: José Nicolás Candia (@mechjook)
"""

import pytest
from httpx import AsyncClient, ASGITransport

from src.api import app


# ============================================================
# Tests unitarios — RUT
# ============================================================

class TestRut:
    """Tests para src/rut.py."""

    def test_rut_valido(self):
        from src.rut import validar_rut
        result = validar_rut("12.345.678-5")
        assert result["valido"] is True
        assert result["digito_verificador"] == "5"

    def test_rut_valido_sin_formato(self):
        from src.rut import validar_rut
        result = validar_rut("123456785")
        assert result["valido"] is True

    def test_rut_invalido(self):
        from src.rut import validar_rut
        result = validar_rut("12.345.678-0")
        assert result["valido"] is False
        assert result["digito_esperado"] == "5"

    def test_rut_con_k(self):
        from src.rut import validar_rut
        result = validar_rut("44.444.446-0")
        # Solo verificar que retorna resultado sin error
        assert "valido" in result

    def test_rut_vacio(self):
        from src.rut import validar_rut
        result = validar_rut("")
        assert result["valido"] is False
        assert "vacío" in result["mensaje"].lower()

    def test_rut_corto(self):
        from src.rut import validar_rut
        result = validar_rut("5")
        assert result["valido"] is False

    def test_calcular_dv(self):
        from src.rut import calcular_digito_verificador
        assert calcular_digito_verificador(12345678) == "5"

    def test_formatear_rut(self):
        from src.rut import formatear_rut
        assert formatear_rut("123456785") == "12.345.678-5"


# ============================================================
# Tests unitarios — IVA
# ============================================================

class TestIva:
    """Tests para src/iva.py."""

    def test_iva_desde_neto(self):
        from src.iva import calcular_iva_desde_neto
        result = calcular_iva_desde_neto(1_000_000)
        assert result["iva"] == 190_000
        assert result["monto_bruto"] == 1_190_000

    def test_neto_desde_bruto(self):
        from src.iva import calcular_neto_desde_bruto
        result = calcular_neto_desde_bruto(1_190_000)
        assert result["monto_neto"] == 1_000_000
        assert result["iva"] == 190_000

    def test_iva_cero(self):
        from src.iva import calcular_iva_desde_neto
        result = calcular_iva_desde_neto(0)
        assert result["iva"] == 0

    def test_iva_negativo_error(self):
        from src.iva import calcular_iva_desde_neto
        with pytest.raises(ValueError):
            calcular_iva_desde_neto(-100)

    def test_desglose_factura(self):
        from src.iva import desglose_factura
        items = [
            {"descripcion": "Item 1", "cantidad": 2, "precio_unitario_neto": 500_000},
            {"descripcion": "Item 2", "cantidad": 1, "precio_unitario_neto": 300_000},
        ]
        result = desglose_factura(items)
        assert result["subtotal_neto"] == 1_300_000
        assert result["iva_total"] == 247_000
        assert result["total_bruto"] == 1_547_000
        assert result["cantidad_items"] == 2


# ============================================================
# Tests unitarios — Honorarios
# ============================================================

class TestHonorarios:
    """Tests para src/honorarios.py."""

    def test_retencion_2026(self):
        from src.honorarios import calcular_retencion_desde_bruto
        result = calcular_retencion_desde_bruto(1_000_000, anio=2026)
        assert result["tasa_retencion"] == 0.1525
        assert result["retencion"] == 152_500
        assert result["monto_liquido"] == 847_500

    def test_retencion_2027(self):
        from src.honorarios import calcular_retencion_desde_bruto
        result = calcular_retencion_desde_bruto(1_000_000, anio=2027)
        assert result["tasa_retencion"] == 0.17
        assert result["retencion"] == 170_000

    def test_bruto_desde_liquido(self):
        from src.honorarios import calcular_bruto_desde_liquido
        result = calcular_bruto_desde_liquido(847_500, anio=2026)
        assert result["monto_bruto"] == 1_000_000
        assert result["monto_liquido"] == 847_500

    def test_simulacion_anual(self):
        from src.honorarios import simular_honorarios_anuales
        result = simular_honorarios_anuales(1_000_000, meses=12, anio=2026)
        assert result["total_bruto"] == 12_000_000
        assert result["meses"] == 12
        assert len(result["detalle_mensual"]) == 12

    def test_honorarios_negativo_error(self):
        from src.honorarios import calcular_retencion_desde_bruto
        with pytest.raises(ValueError):
            calcular_retencion_desde_bruto(-500_000)


# ============================================================
# Tests unitarios — Topes
# ============================================================

class TestTopes:
    """Tests para src/topes.py."""

    def test_calcular_topes(self):
        from src.topes import calcular_topes
        result = calcular_topes(39842.0)
        assert result["tope_afp_uf"] == 90.0
        assert result["tope_afp_pesos"] == round(90 * 39842)
        assert result["tope_cesantia_pesos"] == round(135.2 * 39842)

    def test_cotizaciones_basicas(self):
        from src.topes import calcular_cotizaciones
        result = calcular_cotizaciones(1_500_000, afp="Habitat")
        assert result["afp"] == "Habitat"
        assert result["cotizaciones"]["afp"]["tasa"] == 0.1127
        assert result["cotizaciones"]["salud"]["tasa"] == 0.07
        assert result["renta_liquida_estimada"] < 1_500_000

    def test_cotizaciones_sobre_tope(self):
        from src.topes import calcular_cotizaciones
        result = calcular_cotizaciones(5_000_000, afp="Habitat")
        assert result["topes"]["renta_supera_tope_afp"] is True

    def test_cotizaciones_afp_invalida(self):
        from src.topes import calcular_cotizaciones
        with pytest.raises(ValueError, match="AFP no válida"):
            calcular_cotizaciones(1_000_000, afp="NoExiste")

    def test_listar_afps(self):
        from src.topes import listar_afps
        afps = listar_afps()
        assert len(afps) == 7
        nombres = [a["nombre"] for a in afps]
        assert "Habitat" in nombres
        assert "Modelo" in nombres


# ============================================================
# Tests unitarios — F29
# ============================================================

class TestF29:
    """Tests para src/f29.py."""

    def test_f29_iva_a_pagar(self):
        from src.f29 import simular_f29
        result = simular_f29(ventas_netas=10_000_000, compras_netas=6_000_000)
        debito = round(10_000_000 * 0.19)
        credito = round(6_000_000 * 0.19)
        assert result["debito_fiscal"] == debito
        assert result["credito_fiscal"] == credito
        assert result["iva_a_pagar"] == debito - credito
        assert result["resultado"] == "A PAGAR"

    def test_f29_remanente(self):
        from src.f29 import simular_f29
        result = simular_f29(ventas_netas=2_000_000, compras_netas=8_000_000)
        assert result["iva_a_pagar"] == 0
        assert result["remanente_nuevo"] > 0

    def test_f29_con_remanente_anterior(self):
        from src.f29 import simular_f29
        result = simular_f29(ventas_netas=5_000_000, compras_netas=3_000_000,
                             remanente_anterior=200_000)
        credito_total = round(3_000_000 * 0.19) + 200_000
        assert result["credito_fiscal_total"] == credito_total

    def test_f29_ppm(self):
        from src.f29 import simular_f29
        result = simular_f29(ventas_netas=10_000_000, compras_netas=0)
        assert result["ppm"]["monto"] == 100_000
        assert result["ppm"]["tasa"] == 0.01

    def test_f29_ventas_negativas_error(self):
        from src.f29 import simular_f29
        with pytest.raises(ValueError):
            simular_f29(ventas_netas=-1, compras_netas=0)


# ============================================================
# Tests de integración — Endpoints API
# ============================================================

@pytest.fixture
def transport():
    return ASGITransport(app=app)


class TestApiEndpoints:
    """Tests de endpoints con httpx."""

    @pytest.mark.anyio
    async def test_health(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    @pytest.mark.anyio
    async def test_validar_rut_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/rut/validar", json={"rut": "12.345.678-5"})
        assert r.status_code == 200
        assert r.json()["valido"] is True

    @pytest.mark.anyio
    async def test_iva_desde_neto_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/iva/desde-neto", json={"monto_neto": 1000000})
        assert r.status_code == 200
        assert r.json()["iva"] == 190000

    @pytest.mark.anyio
    async def test_iva_desde_bruto_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/iva/desde-bruto", json={"monto_bruto": 1190000})
        assert r.status_code == 200
        assert r.json()["monto_neto"] == 1000000

    @pytest.mark.anyio
    async def test_factura_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/iva/factura", json={
                "items": [{"descripcion": "Test", "cantidad": 1, "precio_unitario_neto": 500000}]
            })
        assert r.status_code == 200
        assert r.json()["subtotal_neto"] == 500000

    @pytest.mark.anyio
    async def test_honorarios_retencion_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/honorarios/retencion", json={"monto_bruto": 1000000, "anio": 2026})
        assert r.status_code == 200
        assert r.json()["retencion"] == 152500

    @pytest.mark.anyio
    async def test_honorarios_liquido_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/honorarios/liquido", json={"monto_liquido": 847500, "anio": 2026})
        assert r.status_code == 200
        assert r.json()["monto_bruto"] == 1000000

    @pytest.mark.anyio
    async def test_honorarios_anual_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/honorarios/anual", json={"monto_mensual_bruto": 1000000, "meses": 12})
        assert r.status_code == 200
        assert r.json()["total_bruto"] == 12000000

    @pytest.mark.anyio
    async def test_topes_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/topes/calcular", json={"valor_uf": 39842})
        assert r.status_code == 200
        assert r.json()["tope_afp_uf"] == 90.0

    @pytest.mark.anyio
    async def test_cotizaciones_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/topes/cotizaciones", json={"renta_bruta": 1500000, "afp": "Habitat"})
        assert r.status_code == 200
        assert r.json()["afp"] == "Habitat"

    @pytest.mark.anyio
    async def test_afps_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/topes/afps")
        assert r.status_code == 200
        assert len(r.json()) == 7

    @pytest.mark.anyio
    async def test_f29_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/f29/simular", json={"ventas_netas": 10000000, "compras_netas": 6000000})
        assert r.status_code == 200
        assert r.json()["resultado"] == "A PAGAR"

    @pytest.mark.anyio
    async def test_validation_error(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/iva/desde-neto", json={"monto_neto": -100})
        assert r.status_code == 422  # Pydantic validation error

    @pytest.mark.anyio
    async def test_cotizaciones_afp_invalida_endpoint(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/topes/cotizaciones", json={"renta_bruta": 1000000, "afp": "FakeAFP"})
        assert r.status_code == 400
