"""
Simulador simplificado del Formulario 29 (F29) — Declaración de IVA.

El F29 es la declaración mensual de IVA que presentan los contribuyentes
al SII (Servicio de Impuestos Internos) de Chile.

Cálculo simplificado:
  - Débito Fiscal = IVA de las ventas del período
  - Crédito Fiscal = IVA de las compras del período
  - IVA a pagar = Débito - Crédito (si > 0)
  - Remanente = Crédito - Débito (si crédito > débito, se arrastra)

PPM (Pago Provisional Mensual):
  - Tasa sobre ventas netas (generalmente 1% para empresas régimen general)

Autor: José Nicolás Candia (@mechjook)
"""

TASA_IVA = 0.19
TASA_PPM_DEFAULT = 0.01  # 1% PPM general


def calcular_debito_fiscal(ventas_netas: float, ventas_exentas: float = 0) -> dict:
    """
    Calcula el débito fiscal del período.

    Args:
        ventas_netas: Total de ventas afectas a IVA (neto)
        ventas_exentas: Total de ventas exentas de IVA

    Returns:
        dict con ventas_netas, ventas_exentas, debito_fiscal
    """
    if ventas_netas < 0:
        raise ValueError("Las ventas netas no pueden ser negativas")
    if ventas_exentas < 0:
        raise ValueError("Las ventas exentas no pueden ser negativas")

    debito = round(ventas_netas * TASA_IVA)

    return {
        "ventas_netas": round(ventas_netas),
        "ventas_exentas": round(ventas_exentas),
        "ventas_totales": round(ventas_netas + ventas_exentas),
        "debito_fiscal": debito,
    }


def calcular_credito_fiscal(compras_netas: float, compras_activo_fijo: float = 0) -> dict:
    """
    Calcula el crédito fiscal del período.

    Args:
        compras_netas: Total de compras afectas a IVA (neto)
        compras_activo_fijo: Compras de activo fijo con IVA recuperable

    Returns:
        dict con compras_netas, credito_fiscal, credito_activo_fijo
    """
    if compras_netas < 0:
        raise ValueError("Las compras netas no pueden ser negativas")
    if compras_activo_fijo < 0:
        raise ValueError("Las compras de activo fijo no pueden ser negativas")

    credito = round(compras_netas * TASA_IVA)
    credito_af = round(compras_activo_fijo * TASA_IVA)

    return {
        "compras_netas": round(compras_netas),
        "compras_activo_fijo": round(compras_activo_fijo),
        "credito_fiscal": credito,
        "credito_activo_fijo": credito_af,
        "credito_fiscal_total": credito + credito_af,
    }


def simular_f29(ventas_netas: float, compras_netas: float,
                ventas_exentas: float = 0,
                compras_activo_fijo: float = 0,
                remanente_anterior: float = 0,
                tasa_ppm: float = TASA_PPM_DEFAULT,
                retenciones_honorarios: float = 0) -> dict:
    """
    Simula la declaración completa del F29.

    Args:
        ventas_netas: Ventas afectas netas del período
        compras_netas: Compras afectas netas del período
        ventas_exentas: Ventas exentas del período
        compras_activo_fijo: Compras de activo fijo del período
        remanente_anterior: Remanente de crédito fiscal del mes anterior
        tasa_ppm: Tasa de PPM (default 1%)
        retenciones_honorarios: Retenciones de boletas de honorarios pagadas

    Returns:
        dict con desglose completo del F29
    """
    if ventas_netas < 0:
        raise ValueError("Las ventas netas no pueden ser negativas")
    if compras_netas < 0:
        raise ValueError("Las compras netas no pueden ser negativas")

    # Débito fiscal
    debito = calcular_debito_fiscal(ventas_netas, ventas_exentas)

    # Crédito fiscal
    credito = calcular_credito_fiscal(compras_netas, compras_activo_fijo)

    # Remanente anterior
    credito_total = credito["credito_fiscal_total"] + round(remanente_anterior)

    # Determinación de IVA
    iva_determinado = debito["debito_fiscal"] - credito_total

    if iva_determinado > 0:
        iva_a_pagar = iva_determinado
        remanente_nuevo = 0
    else:
        iva_a_pagar = 0
        remanente_nuevo = abs(iva_determinado)

    # PPM
    ppm = round(ventas_netas * tasa_ppm)

    # Total a pagar
    total_a_pagar = iva_a_pagar + ppm - round(retenciones_honorarios)
    if total_a_pagar < 0:
        total_a_pagar = 0  # Saldo a favor

    return {
        "periodo": {
            "ventas_netas": round(ventas_netas),
            "ventas_exentas": round(ventas_exentas),
            "compras_netas": round(compras_netas),
            "compras_activo_fijo": round(compras_activo_fijo),
        },
        "debito_fiscal": debito["debito_fiscal"],
        "credito_fiscal": credito["credito_fiscal_total"],
        "remanente_anterior": round(remanente_anterior),
        "credito_fiscal_total": credito_total,
        "iva_determinado": iva_determinado,
        "iva_a_pagar": iva_a_pagar,
        "remanente_nuevo": remanente_nuevo,
        "ppm": {
            "tasa": tasa_ppm,
            "tasa_porcentaje": f"{tasa_ppm * 100:.1f}%",
            "monto": ppm,
        },
        "retenciones_honorarios": round(retenciones_honorarios),
        "total_a_pagar": total_a_pagar,
        "resultado": "A PAGAR" if total_a_pagar > 0 else "SIN PAGO",
    }
