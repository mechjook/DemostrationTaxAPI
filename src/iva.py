"""
Cálculo de IVA (Impuesto al Valor Agregado) — Chile 19%.

Funcionalidades:
  - Calcular IVA desde monto neto
  - Calcular neto desde monto bruto (con IVA incluido)
  - Desglose completo: neto + IVA = bruto
  - Cálculo con tasas especiales (exento, construcción 65%)

Autor: José Nicolás Candia (@mechjook)
"""

TASA_IVA_ESTANDAR = 0.19
TASA_IVA_CONSTRUCCION = 0.65  # 65% del IVA en crédito especial


def calcular_iva_desde_neto(monto_neto: float, tasa: float = TASA_IVA_ESTANDAR) -> dict:
    """
    Calcula IVA y bruto a partir del monto neto.

    Args:
        monto_neto: Monto sin IVA
        tasa: Tasa de IVA (default 0.19 = 19%)

    Returns:
        dict con neto, iva, bruto, tasa
    """
    if monto_neto < 0:
        raise ValueError("El monto neto no puede ser negativo")
    if not 0 <= tasa <= 1:
        raise ValueError("La tasa debe estar entre 0 y 1")

    iva = round(monto_neto * tasa)
    bruto = monto_neto + iva

    return {
        "monto_neto": round(monto_neto),
        "iva": iva,
        "monto_bruto": round(bruto),
        "tasa_iva": tasa,
        "tasa_iva_porcentaje": f"{tasa * 100:.0f}%",
    }


def calcular_neto_desde_bruto(monto_bruto: float, tasa: float = TASA_IVA_ESTANDAR) -> dict:
    """
    Calcula monto neto e IVA a partir del monto bruto (IVA incluido).

    Args:
        monto_bruto: Monto con IVA incluido
        tasa: Tasa de IVA (default 0.19 = 19%)

    Returns:
        dict con neto, iva, bruto, tasa
    """
    if monto_bruto < 0:
        raise ValueError("El monto bruto no puede ser negativo")
    if not 0 <= tasa <= 1:
        raise ValueError("La tasa debe estar entre 0 y 1")

    neto = round(monto_bruto / (1 + tasa))
    iva = monto_bruto - neto

    return {
        "monto_neto": neto,
        "iva": round(iva),
        "monto_bruto": round(monto_bruto),
        "tasa_iva": tasa,
        "tasa_iva_porcentaje": f"{tasa * 100:.0f}%",
    }


def desglose_factura(items: list[dict]) -> dict:
    """
    Genera desglose completo de una factura con múltiples items.

    Cada item debe tener: {"descripcion": str, "cantidad": int, "precio_unitario_neto": float}

    Returns:
        dict con items detallados, subtotal_neto, iva_total, total_bruto
    """
    detalle = []
    subtotal_neto = 0

    for item in items:
        descripcion = item.get("descripcion", "")
        cantidad = item.get("cantidad", 1)
        precio_unitario = item.get("precio_unitario_neto", 0)

        if cantidad < 0:
            raise ValueError(f"Cantidad negativa en item '{descripcion}'")
        if precio_unitario < 0:
            raise ValueError(f"Precio negativo en item '{descripcion}'")

        neto_linea = round(cantidad * precio_unitario)
        iva_linea = round(neto_linea * TASA_IVA_ESTANDAR)

        detalle.append({
            "descripcion": descripcion,
            "cantidad": cantidad,
            "precio_unitario_neto": round(precio_unitario),
            "neto_linea": neto_linea,
            "iva_linea": iva_linea,
            "total_linea": neto_linea + iva_linea,
        })
        subtotal_neto += neto_linea

    iva_total = round(subtotal_neto * TASA_IVA_ESTANDAR)

    return {
        "detalle": detalle,
        "subtotal_neto": subtotal_neto,
        "iva_total": iva_total,
        "total_bruto": subtotal_neto + iva_total,
        "tasa_iva": TASA_IVA_ESTANDAR,
        "cantidad_items": len(items),
    }
