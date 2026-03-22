"""
Simulador de Retención de Honorarios — Boletas a Terceros.

En Chile, las boletas de honorarios tienen una retención de impuesto
que ha ido variando según la reforma tributaria:

  - 2024: 13.75%
  - 2025: 14.50%
  - 2026: 15.25%
  - 2027+: 17.00% (tasa final)

El pagador retiene el porcentaje y lo entera al SII.
El prestador recibe el monto líquido (bruto - retención).

Autor: José Nicolás Candia (@mechjook)
"""

TASAS_RETENCION = {
    2024: 0.1375,
    2025: 0.1450,
    2026: 0.1525,
    2027: 0.1700,
}


def obtener_tasa_retencion(anio: int) -> float:
    """Retorna la tasa de retención vigente para el año indicado."""
    if anio < 2024:
        return 0.1375  # Tasa anterior
    if anio >= 2027:
        return 0.1700  # Tasa final
    return TASAS_RETENCION.get(anio, 0.1700)


def calcular_retencion_desde_bruto(monto_bruto: float, anio: int = 2026) -> dict:
    """
    Calcula la retención y líquido desde el monto bruto de la boleta.

    Args:
        monto_bruto: Monto total de la boleta de honorarios
        anio: Año para determinar la tasa de retención

    Returns:
        dict con bruto, retencion, liquido, tasa
    """
    if monto_bruto < 0:
        raise ValueError("El monto bruto no puede ser negativo")

    tasa = obtener_tasa_retencion(anio)
    retencion = round(monto_bruto * tasa)
    liquido = monto_bruto - retencion

    return {
        "monto_bruto": round(monto_bruto),
        "retencion": retencion,
        "monto_liquido": round(liquido),
        "tasa_retencion": tasa,
        "tasa_retencion_porcentaje": f"{tasa * 100:.2f}%",
        "anio": anio,
    }


def calcular_bruto_desde_liquido(monto_liquido: float, anio: int = 2026) -> dict:
    """
    Calcula el monto bruto necesario para recibir un líquido deseado.

    Fórmula: bruto = liquido / (1 - tasa)

    Args:
        monto_liquido: Monto líquido deseado
        anio: Año para determinar la tasa de retención

    Returns:
        dict con bruto, retencion, liquido, tasa
    """
    if monto_liquido < 0:
        raise ValueError("El monto líquido no puede ser negativo")

    tasa = obtener_tasa_retencion(anio)
    bruto = round(monto_liquido / (1 - tasa))
    retencion = bruto - round(monto_liquido)

    return {
        "monto_bruto": bruto,
        "retencion": retencion,
        "monto_liquido": round(monto_liquido),
        "tasa_retencion": tasa,
        "tasa_retencion_porcentaje": f"{tasa * 100:.2f}%",
        "anio": anio,
    }


def simular_honorarios_anuales(monto_mensual_bruto: float, meses: int = 12,
                                anio: int = 2026) -> dict:
    """
    Simula el total anual de honorarios con retenciones acumuladas.

    Args:
        monto_mensual_bruto: Monto bruto mensual de la boleta
        meses: Cantidad de meses a simular
        anio: Año tributario

    Returns:
        dict con detalle mensual y totales anuales
    """
    if monto_mensual_bruto < 0:
        raise ValueError("El monto mensual no puede ser negativo")
    if not 1 <= meses <= 12:
        raise ValueError("Los meses deben estar entre 1 y 12")

    tasa = obtener_tasa_retencion(anio)
    detalle_mensual = []
    total_bruto = 0
    total_retencion = 0
    total_liquido = 0

    for mes in range(1, meses + 1):
        retencion = round(monto_mensual_bruto * tasa)
        liquido = monto_mensual_bruto - retencion
        total_bruto += monto_mensual_bruto
        total_retencion += retencion
        total_liquido += liquido

        detalle_mensual.append({
            "mes": mes,
            "bruto": round(monto_mensual_bruto),
            "retencion": retencion,
            "liquido": round(liquido),
        })

    return {
        "detalle_mensual": detalle_mensual,
        "total_bruto": round(total_bruto),
        "total_retencion": round(total_retencion),
        "total_liquido": round(total_liquido),
        "tasa_retencion": tasa,
        "tasa_retencion_porcentaje": f"{tasa * 100:.2f}%",
        "anio": anio,
        "meses": meses,
    }
