"""
Cálculo de Topes Imponibles — AFP, Salud y Seguro de Cesantía.

Los topes imponibles en Chile limitan la base sobre la cual se calculan
las cotizaciones previsionales. Se expresan en UF y se actualizan mensualmente.

Valores de referencia (Marzo 2026):
  - UF: ~$39.842
  - Tope AFP:       90 UF    → $3.585.780
  - Tope IPS:       60 UF    → $2.390.520
  - Tope Cesantía: 135.2 UF  → $5.386.641
  - Renta mínima imponible:   $539.000

Tasas de cotización AFP (cargo trabajador):
  - Capital:    11.44%
  - Cuprum:     11.44%
  - Habitat:    11.27%
  - PlanVital:  11.16%
  - ProVida:    11.45%
  - Modelo:     10.58%
  - Uno:        10.69%

Autor: José Nicolás Candia (@mechjook)
"""

# Valor UF referencial (se puede actualizar)
UF_REFERENCIA = 39842.0

# Topes en UF
TOPE_AFP_UF = 90.0
TOPE_IPS_UF = 60.0
TOPE_CESANTIA_UF = 135.2

# Renta mínima imponible
RENTA_MINIMA_IMPONIBLE = 539_000

# Tasas AFP (% cargo trabajador, incluye comisión)
TASAS_AFP = {
    "Capital": {"tasa_trabajador": 0.1144, "tasa_empleador": 0.0, "sis": 0.0154},
    "Cuprum": {"tasa_trabajador": 0.1144, "tasa_empleador": 0.0, "sis": 0.0154},
    "Habitat": {"tasa_trabajador": 0.1127, "tasa_empleador": 0.0, "sis": 0.0154},
    "PlanVital": {"tasa_trabajador": 0.1116, "tasa_empleador": 0.0, "sis": 0.0154},
    "ProVida": {"tasa_trabajador": 0.1145, "tasa_empleador": 0.0, "sis": 0.0154},
    "Modelo": {"tasa_trabajador": 0.1058, "tasa_empleador": 0.0, "sis": 0.0154},
    "Uno": {"tasa_trabajador": 0.1069, "tasa_empleador": 0.0, "sis": 0.0154},
}

# Tasa salud (Fonasa)
TASA_SALUD = 0.07

# Tasas AFC (Seguro de Cesantía)
AFC_INDEFINIDO = {"trabajador": 0.006, "empleador": 0.024}
AFC_PLAZO_FIJO = {"trabajador": 0.0, "empleador": 0.03}
AFC_INDEFINIDO_11_ANIOS = {"trabajador": 0.006, "empleador": 0.024}
AFC_CASA_PARTICULAR = {"trabajador": 0.0, "empleador": 0.03}


def calcular_topes(valor_uf: float = UF_REFERENCIA) -> dict:
    """Calcula los topes imponibles en pesos según el valor de la UF."""
    return {
        "valor_uf": round(valor_uf, 2),
        "tope_afp_uf": TOPE_AFP_UF,
        "tope_afp_pesos": round(TOPE_AFP_UF * valor_uf),
        "tope_ips_uf": TOPE_IPS_UF,
        "tope_ips_pesos": round(TOPE_IPS_UF * valor_uf),
        "tope_cesantia_uf": TOPE_CESANTIA_UF,
        "tope_cesantia_pesos": round(TOPE_CESANTIA_UF * valor_uf),
        "renta_minima_imponible": RENTA_MINIMA_IMPONIBLE,
    }


def calcular_cotizaciones(renta_bruta: float, afp: str = "Habitat",
                          tipo_contrato: str = "indefinido",
                          valor_uf: float = UF_REFERENCIA) -> dict:
    """
    Calcula todas las cotizaciones previsionales de un trabajador dependiente.

    Args:
        renta_bruta: Renta bruta mensual en pesos
        afp: Nombre de la AFP
        tipo_contrato: "indefinido" o "plazo_fijo"
        valor_uf: Valor de la UF

    Returns:
        dict con desglose completo de cotizaciones
    """
    if renta_bruta < 0:
        raise ValueError("La renta bruta no puede ser negativa")

    afp_upper = afp.strip().title()
    if afp_upper not in TASAS_AFP:
        raise ValueError(f"AFP no válida: {afp}. Opciones: {', '.join(TASAS_AFP.keys())}")

    topes = calcular_topes(valor_uf)

    # Aplicar topes
    base_afp = min(renta_bruta, topes["tope_afp_pesos"])
    base_salud = min(renta_bruta, topes["tope_afp_pesos"])  # Mismo tope que AFP
    base_cesantia = min(renta_bruta, topes["tope_cesantia_pesos"])

    # AFP
    tasa_afp = TASAS_AFP[afp_upper]["tasa_trabajador"]
    cotizacion_afp = round(base_afp * tasa_afp)

    # SIS (Seguro de Invalidez y Sobrevivencia — cargo empleador)
    sis = round(base_afp * TASAS_AFP[afp_upper]["sis"])

    # Salud (7%)
    cotizacion_salud = round(base_salud * TASA_SALUD)

    # AFC
    afc_tasas = AFC_INDEFINIDO if tipo_contrato == "indefinido" else AFC_PLAZO_FIJO
    afc_trabajador = round(base_cesantia * afc_tasas["trabajador"])
    afc_empleador = round(base_cesantia * afc_tasas["empleador"])

    # Totales
    total_descuentos_trabajador = cotizacion_afp + cotizacion_salud + afc_trabajador
    total_costo_empleador = sis + afc_empleador
    renta_liquida_estimada = round(renta_bruta - total_descuentos_trabajador)

    return {
        "renta_bruta": round(renta_bruta),
        "afp": afp_upper,
        "tipo_contrato": tipo_contrato,
        "valor_uf": round(valor_uf, 2),
        "topes": {
            "base_afp": round(base_afp),
            "base_salud": round(base_salud),
            "base_cesantia": round(base_cesantia),
            "renta_supera_tope_afp": renta_bruta > topes["tope_afp_pesos"],
            "renta_supera_tope_cesantia": renta_bruta > topes["tope_cesantia_pesos"],
        },
        "cotizaciones": {
            "afp": {"tasa": tasa_afp, "monto": cotizacion_afp, "cargo": "trabajador"},
            "salud": {"tasa": TASA_SALUD, "monto": cotizacion_salud, "cargo": "trabajador"},
            "afc_trabajador": {"tasa": afc_tasas["trabajador"], "monto": afc_trabajador, "cargo": "trabajador"},
            "afc_empleador": {"tasa": afc_tasas["empleador"], "monto": afc_empleador, "cargo": "empleador"},
            "sis": {"tasa": TASAS_AFP[afp_upper]["sis"], "monto": sis, "cargo": "empleador"},
        },
        "total_descuentos_trabajador": total_descuentos_trabajador,
        "total_costo_empleador": total_costo_empleador,
        "renta_liquida_estimada": renta_liquida_estimada,
    }


def listar_afps() -> list[dict]:
    """Retorna lista de AFPs con sus tasas."""
    return [
        {"nombre": nombre, **tasas}
        for nombre, tasas in TASAS_AFP.items()
    ]
