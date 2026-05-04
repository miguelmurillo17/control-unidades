from .models import Movimiento, Unidad, UnidadMovimiento

# Transiciones válidas por tipo de último movimiento
_TRANSICIONES_VALIDAS = {
    None:             {"ENTRADA"},
    "ENTRADA":        {"SALIDA", "TALLER_ENTRADA"},
    "SALIDA":         {"ENTRADA"},
    "TALLER_ENTRADA": {"TALLER_SALIDA"},
    "TALLER_SALIDA":  {"ENTRADA", "SALIDA"},
    "CORRECCION":     {"ENTRADA", "SALIDA", "TALLER_ENTRADA", "TALLER_SALIDA"},
}

_DESCRIPCIONES = {
    "ENTRADA":        "Entrada",
    "SALIDA":         "Salida",
    "TALLER_ENTRADA": "Entrada a taller",
    "TALLER_SALIDA":  "Salida de taller",
}


def detectar_inconsistencia(unidad: Unidad, tipo: str) -> str:
    """Devuelve mensaje de advertencia si el movimiento rompe la lógica esperada, o '' si es consistente."""
    ultimo = (
        Movimiento.objects
        .filter(unidad_movimientos__unidad=unidad, cancelado=False)
        .order_by("-fecha_hora_evento")
        .first()
    )
    ultimo_tipo = ultimo.tipo if ultimo else None
    validos = _TRANSICIONES_VALIDAS.get(ultimo_tipo, set())

    if tipo in validos:
        return ""

    if ultimo_tipo is None:
        return f"{unidad.numero_economico}: sin movimientos previos, se esperaba una Entrada."

    return (
        f"{unidad.numero_economico}: el último movimiento fue "
        f"«{_DESCRIPCIONES.get(ultimo_tipo, ultimo_tipo)}» — "
        f"registrar «{_DESCRIPCIONES.get(tipo, tipo)}» puede ser incorrecto."
    )


def detectar_inconsistencias(unidades, tipo: str) -> list[str]:
    """Revisa cada unidad y devuelve lista de advertencias."""
    return [msg for u in unidades if (msg := detectar_inconsistencia(u, tipo))]


def crear_movimiento(form_data: dict, usuario) -> Movimiento:
    """
    Crea y persiste un movimiento para 1–3 unidades.
    1. Detecta inconsistencias por unidad (no bloquea el guardado).
    2. Actualiza sucursal_actual en unidades que quedan ubicadas en sucursal.
    """
    unidades = form_data["unidades"]
    tipo     = form_data["tipo"]
    sucursal = form_data["sucursal"]

    advertencias = detectar_inconsistencias(unidades, tipo)
    inconsistente = bool(advertencias)

    movimiento = Movimiento.objects.create(
        tipo=tipo,
        sucursal=sucursal,
        fecha_hora_evento=form_data["fecha_hora_evento"],
        usuario=usuario,
        observaciones=form_data.get("observaciones", ""),
        inconsistente=inconsistente,
    )
    for unidad in unidades:
        UnidadMovimiento.objects.create(movimiento=movimiento, unidad=unidad)

    # Actualizar sucursal_actual en unidades que quedan en una ubicación
    if tipo in ("ENTRADA", "TALLER_ENTRADA"):
        ids = [u.pk for u in unidades]
        Unidad.objects.filter(pk__in=ids).update(sucursal_actual=sucursal)

    return movimiento
