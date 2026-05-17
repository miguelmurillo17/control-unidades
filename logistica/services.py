from .models import Movimiento, Unidad, UnidadMovimiento, Inspeccion, SubInspeccion

# Condición por tipo de sub-inspección.
# Recibe el objeto Inspeccion ya creado (con acceso a movimiento, manifiesto, unidades…).
# Retorna True si ese tipo aplica para esta inspección.
# Programar condiciones reales en una etapa posterior.
CONDICIONES_SUB_INSPECCION = {
    "GENERAL":           lambda inspeccion: True,
    "CAJA":              lambda inspeccion: True,
    "CAJA_VACIA":        lambda inspeccion: True,
    "LLANTAS":           lambda inspeccion: True,
    "CINCO_PUNTOS":      lambda inspeccion: True,
    "DIECINUEVE_PUNTOS": lambda inspeccion: True,
    "CANINA":            lambda inspeccion: True,
    "MEDIDAS_REMOLQUE":  lambda inspeccion: True,
}


def sub_tipos_aplicables(inspeccion: Inspeccion) -> list[str]:
    return [tipo for tipo, cond in CONDICIONES_SUB_INSPECCION.items() if cond(inspeccion)]


def crear_inspeccion(movimiento: Movimiento) -> Inspeccion:
    inspeccion = Inspeccion.objects.create(movimiento=movimiento)
    tipos = sub_tipos_aplicables(inspeccion)
    SubInspeccion.objects.bulk_create([
        SubInspeccion(inspeccion=inspeccion, tipo=tipo)
        for tipo in tipos
    ])
    return inspeccion

# Transiciones válidas por tipo de último movimiento
_TRANSICIONES_VALIDAS = {
    None:             {"ENTRADA"},
    "ENTRADA":        {"SALIDA", "TALLER_ENTRADA", "INSPECCION"},
    "SALIDA":         {"ENTRADA", "INSPECCION"},
    "TALLER_ENTRADA": {"TALLER_SALIDA", "INSPECCION"},
    "TALLER_SALIDA":  {"ENTRADA", "SALIDA", "INSPECCION"},
    "CORRECCION":     {"ENTRADA", "SALIDA", "TALLER_ENTRADA", "TALLER_SALIDA", "INSPECCION"},
    "INSPECCION":     {"ENTRADA", "SALIDA", "TALLER_ENTRADA", "TALLER_SALIDA", "INSPECCION"},
}

_DESCRIPCIONES = {
    "ENTRADA":        "Entrada",
    "SALIDA":         "Salida",
    "TALLER_ENTRADA": "Entrada a taller",
    "TALLER_SALIDA":  "Salida de taller",
    "INSPECCION":     "Inspección",
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
        manifiesto=form_data.get("manifiesto"),
        fecha_hora_evento=form_data["fecha_hora_evento"],
        usuario=usuario,
        observaciones=form_data.get("observaciones", ""),
        inconsistente=inconsistente,
    )
    for unidad in unidades:
        UnidadMovimiento.objects.create(movimiento=movimiento, unidad=unidad)

    if tipo in ("ENTRADA", "TALLER_ENTRADA"):
        ids = [u.pk for u in unidades]
        Unidad.objects.filter(pk__in=ids).update(sucursal_actual=sucursal)

    if tipo == "INSPECCION":
        crear_inspeccion(movimiento)

    return movimiento
