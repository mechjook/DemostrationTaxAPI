"""
Validación de RUT chileno.

El RUT (Rol Único Tributario) es el identificador fiscal de Chile.
Formato: XX.XXX.XXX-D donde D es el dígito verificador (0-9 o K).

El dígito verificador se calcula con el algoritmo módulo 11:
  1. Se toman los dígitos del RUT de derecha a izquierda
  2. Se multiplican por la serie 2, 3, 4, 5, 6, 7 (cíclica)
  3. Se suman los productos
  4. Se calcula 11 - (suma % 11)
  5. Si el resultado es 11 → "0", si es 10 → "K", sino el dígito

Autor: José Nicolás Candia (@mechjook)
"""

import re


def limpiar_rut(rut: str) -> str:
    """Elimina puntos, guiones y espacios del RUT."""
    return re.sub(r"[.\-\s]", "", rut.strip().upper())


def calcular_digito_verificador(numero: int) -> str:
    """Calcula el dígito verificador de un número de RUT."""
    if numero < 1:
        raise ValueError("El número de RUT debe ser positivo")

    suma = 0
    multiplicador = 2
    temp = numero

    while temp > 0:
        suma += (temp % 10) * multiplicador
        temp //= 10
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2

    resto = 11 - (suma % 11)

    if resto == 11:
        return "0"
    elif resto == 10:
        return "K"
    else:
        return str(resto)


def validar_rut(rut: str) -> dict:
    """
    Valida un RUT chileno completo.

    Acepta formatos: 12.345.678-9, 12345678-9, 123456789

    Retorna dict con:
      - valido: bool
      - rut_formateado: str (XX.XXX.XXX-D)
      - numero: int
      - digito_verificador: str
      - digito_esperado: str
      - mensaje: str
    """
    rut_limpio = limpiar_rut(rut)

    if not rut_limpio:
        return {
            "valido": False,
            "rut_formateado": None,
            "numero": None,
            "digito_verificador": None,
            "digito_esperado": None,
            "mensaje": "RUT vacío",
        }

    # Separar número y dígito verificador
    if len(rut_limpio) < 2:
        return {
            "valido": False,
            "rut_formateado": None,
            "numero": None,
            "digito_verificador": None,
            "digito_esperado": None,
            "mensaje": "RUT demasiado corto",
        }

    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]

    if not cuerpo.isdigit():
        return {
            "valido": False,
            "rut_formateado": None,
            "numero": None,
            "digito_verificador": dv_ingresado,
            "digito_esperado": None,
            "mensaje": "El cuerpo del RUT debe contener solo dígitos",
        }

    numero = int(cuerpo)

    if numero < 1_000_000 or numero > 99_999_999:
        return {
            "valido": False,
            "rut_formateado": None,
            "numero": numero,
            "digito_verificador": dv_ingresado,
            "digito_esperado": None,
            "mensaje": "Número de RUT fuera de rango válido (1.000.000 - 99.999.999)",
        }

    dv_esperado = calcular_digito_verificador(numero)
    es_valido = dv_ingresado == dv_esperado

    # Formatear con puntos y guión
    cuerpo_fmt = f"{numero:,}".replace(",", ".")
    rut_formateado = f"{cuerpo_fmt}-{dv_esperado}"

    return {
        "valido": es_valido,
        "rut_formateado": rut_formateado,
        "numero": numero,
        "digito_verificador": dv_ingresado,
        "digito_esperado": dv_esperado,
        "mensaje": "RUT válido" if es_valido else f"Dígito verificador incorrecto (esperado: {dv_esperado})",
    }


def formatear_rut(rut: str) -> str:
    """Formatea un RUT a la forma XX.XXX.XXX-D."""
    resultado = validar_rut(rut)
    return resultado["rut_formateado"] if resultado["rut_formateado"] else rut
