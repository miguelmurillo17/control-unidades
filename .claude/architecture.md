# Arquitectura del Proyecto — Control de Unidades

```
Repositorio : control-unidades
Django project : config
```

---

## Estructura de Apps

```
config/          ← Configuración del proyecto Django
core/
    usuarios/    ← Usuarios del sistema y roles (AUTH_USER_MODEL)
logistica/       ← Toda la lógica de negocio logística
```

---

## Responsabilidad por App

| App             | Responsabilidad                                                              |
| --------------- | ---------------------------------------------------------------------------- |
| `core.usuarios` | Usuarios del sistema, roles básicos                                          |
| `logistica`     | Sucursales, unidades, movimientos e inspecciones — dominio logístico unificado |

---

## Reglas Arquitectónicas

- Los movimientos son **inmutables** — no se editan, no se eliminan
- Solo se permite **cancelación lógica** (`cancelado = True`)
- El estado de una unidad es **derivado**, nunca almacenado directamente
- La lógica de negocio va en `services.py`, **no en views**
- No duplicar lógica entre apps

---

## Modelos

### `core.usuarios` — `models.py`

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ("CASETA", "Caseta"),
        ("TRAFICO", "Tráfico"),
        ("ADMIN", "Administrador"),
    ]
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)
```

---

### `logistica` — `models.py`

Todos los modelos del dominio logístico viven en `logistica/models.py`.

```python
from django.db import models
from core.usuarios.models import Usuario

class Sucursal(models.Model):
    nombre     = models.CharField(max_length=100)
    ciudad     = models.CharField(max_length=100)
    tipo       = models.CharField(max_length=50, blank=True)
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Unidad(models.Model):
    TIPO_CHOICES = [
        ("TRACTOR",  "Tractor"),
        ("REMOLQUE", "Remolque"),
    ]
    numero_economico = models.CharField(max_length=50, unique=True)
    tipo             = models.CharField(max_length=20, choices=TIPO_CHOICES)
    sucursal_actual  = models.ForeignKey(            # ← se actualiza tras cada movimiento válido
        Sucursal, null=True, blank=True, on_delete=models.SET_NULL
    )
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

# estado_actual no se guarda — se calcula dinámicamente desde Movimiento

class Movimiento(models.Model):
    TIPO_CHOICES = [
        ("ENTRADA",        "Entrada"),
        ("SALIDA",         "Salida"),
        ("TALLER_ENTRADA", "Entrada a taller"),
        ("TALLER_SALIDA",  "Salida de taller"),
        ("CORRECCION",     "Corrección"),
    ]
    unidad                = models.ForeignKey(Unidad,   on_delete=models.PROTECT)
    tipo                  = models.CharField(max_length=30, choices=TIPO_CHOICES)
    sucursal              = models.ForeignKey(Sucursal, on_delete=models.PROTECT)
    fecha_hora_evento     = models.DateTimeField()
    fecha_hora_registro   = models.DateTimeField(auto_now_add=True)
    usuario               = models.ForeignKey(Usuario,  on_delete=models.PROTECT)
    observaciones         = models.TextField(blank=True)
    inconsistente         = models.BooleanField(default=False)  # no bloquea; solo marca
    cancelado             = models.BooleanField(default=False)
    referencia_movimiento = models.ForeignKey(           # apunta al movimiento original en CORRECCION
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )

class Inspeccion(models.Model):
    movimiento        = models.OneToOneField(Movimiento, on_delete=models.CASCADE)
    resultado_general = models.CharField(max_length=50, blank=True)
    observaciones     = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

class DetalleInspeccion(models.Model):
    inspeccion     = models.ForeignKey(Inspeccion, on_delete=models.CASCADE)
    punto_revision = models.CharField(max_length=100)
    resultado      = models.CharField(max_length=20)   # "SI" | "NO" | "NA"
    comentario     = models.TextField(blank=True)
```

---

## Services

La lógica de negocio **no** va en views ni en modelos — va en `logistica/services.py`.

### `logistica.services`

```python
def registrar_movimiento(data: dict) -> Movimiento:
    """
    1. Valida reglas de negocio (sin bloquear el guardado)
    2. Detecta y marca inconsistencias
    3. Crea y persiste el movimiento
    4. NO modifica otros registros directamente
    """
    pass

def obtener_estado_actual(unidad: Unidad) -> dict:
    """
    1. Filtra movimientos cancelados
    2. Toma el último movimiento válido por fecha_hora_evento
    3. Deriva y retorna el estado actual
    """
    pass
```

---

## Flujo de Registro de un Movimiento

```
1. Usuario registra movimiento
        ↓
2. services.registrar_movimiento() valida reglas
        ↓
3. ¿Inconsistencia detectada?
   ├── Sí → movimiento.inconsistente = True  (se guarda igual)
   └── No → continúa normal
        ↓
4. Movimiento guardado (inmutable desde este momento)
        ↓
5. Estado de unidad se recalcula desde historial
```

---

## Reglas Críticas para Copilot

```python
# ✅ CORRECTO — corregir un error
Movimiento.objects.create(tipo="CORRECCION", referencia_movimiento=movimiento_original)

# ❌ NUNCA — editar un movimiento existente
movimiento.tipo = "ENTRADA"
movimiento.save()

# ✅ CORRECTO — cancelar lógicamente
movimiento.cancelado = True
movimiento.save()

# ❌ NUNCA — eliminar registros
movimiento.delete()
```

---

## Exclusiones — No implementar

- GPS o tracking en tiempo real
- Notificaciones automáticas
- Aplicación móvil
- Integraciones con sistemas externos

---

## Criterio de Éxito

> El sistema está listo cuando se puede saber **dónde está cualquier unidad** y entender su **historial completo** sin ambigüedad.
