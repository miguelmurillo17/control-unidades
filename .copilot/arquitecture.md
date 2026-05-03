Este archivo de instrucciones incluye:

- estructura de apps Django
- responsabilidades por app
- modelos sugeridos (con campos clave)
- reglas de diseño
- separación lógica (services)

Puedes pegarlo directo en tu proyecto.

⸻

Proyecto

Repositorio: control-unidades
Django project: config

Sistema: Sistema de Control y Trazabilidad de Unidades

⸻

🧱 Estructura de Apps

Crear las siguientes apps:

core/
usuarios/
logistics/
unidades/
sucursales/
movimientos/
inspecciones/

⸻

📦 Descripción de cada App

core.usuarios

Responsabilidad:

- Usuarios del sistema
- Roles básicos

⸻

logistics.sucursales

Responsabilidad:

- Catálogo de sucursales
- Ubicación operativa

⸻

logistics.unidades

Responsabilidad:

- Tractores y remolques

⸻

logistics.movimientos

Responsabilidad:

- Evento central del sistema
- Registro de entradas/salidas/correcciones

⸻

logistics.inspecciones

Responsabilidad:

- Checklist de inspección
- Evidencia operativa

⸻

🧠 Reglas Arquitectónicas

- Los movimientos son inmutables
- No eliminar registros
- Solo cancelación lógica
- Estado de unidad es derivado
- Lógica de negocio en services.py, no en views
- No duplicar lógica entre apps

⸻

📐 MODELOS POR APP

⸻

🔹 core.usuarios.models

from django.contrib.auth.models import AbstractUser
from django.db import models
class Usuario(AbstractUser):
ROLE_CHOICES = [
("CASETA", "Caseta"),
("TRAFICO", "Tráfico"),
("ADMIN", "Administrador"),
]
rol = models.CharField(max_length=20, choices=ROLE_CHOICES)

⸻

🔹 logistics.sucursales.models

from django.db import models
class Sucursal(models.Model):
nombre = models.CharField(max_length=100)
ciudad = models.CharField(max_length=100)
tipo = models.CharField(max_length=50, blank=True)
activo = models.BooleanField(default=True)
created_at = models.DateTimeField(auto_now_add=True)

⸻

🔹 logistics.unidades.models

from django.db import models
from logistics.sucursales.models import Sucursal
class Unidad(models.Model):
TIPO_CHOICES = [
("TRACTOR", "Tractor"),
("REMOLQUE", "Remolque"),
]
numero_economico = models.CharField(max_length=50, unique=True)
tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
sucursal_actual = models.ForeignKey(
Sucursal,
null=True,
blank=True,
on_delete=models.SET_NULL
)
activo = models.BooleanField(default=True)
created_at = models.DateTimeField(auto_now_add=True)

⚠️ No guardar estado_actual aquí (se calcula).

⸻

🔹 logistics.movimientos.models

from django.db import models
from core.usuarios.models import Usuario
from logistics.unidades.models import Unidad
from logistics.sucursales.models import Sucursal
class Movimiento(models.Model):
TIPO_CHOICES = [
("ENTRADA", "Entrada"),
("SALIDA", "Salida"),
("TALLER_ENTRADA", "Entrada a taller"),
("TALLER_SALIDA", "Salida de taller"),
("CORRECCION", "Corrección"),
]
unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT)
tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT)
fecha_hora_evento = models.DateTimeField()
fecha_hora_registro = models.DateTimeField(auto_now_add=True)
usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
observaciones = models.TextField(blank=True)
inconsistente = models.BooleanField(default=False)
cancelado = models.BooleanField(default=False)
referencia_movimiento = models.ForeignKey(
"self",
null=True,
blank=True,
on_delete=models.SET_NULL
)

⸻

🔹 logistics.inspecciones.models

from django.db import models
from logistics.movimientos.models import Movimiento
class Inspeccion(models.Model):
movimiento = models.OneToOneField(Movimiento, on_delete=models.CASCADE)
resultado_general = models.CharField(max_length=50, blank=True)
observaciones = models.TextField(blank=True)
created_at = models.DateTimeField(auto_now_add=True)

⸻

DetalleInspeccion

class DetalleInspeccion(models.Model):
inspeccion = models.ForeignKey(Inspeccion, on_delete=models.CASCADE)
punto_revision = models.CharField(max_length=100)
resultado = models.CharField(max_length=20) # OK / NO / NA
comentario = models.TextField(blank=True)

⸻

⚙️ SERVICES (MUY IMPORTANTE)

Cada app debe tener services.py.

Ejemplo:

logistics.movimientos.services

def registrar_movimiento(data):
""" - valida reglas - detecta inconsistencias - crea movimiento - NO modifica otros registros
"""
pass

⸻

Estado actual (service)

def obtener_estado_actual(unidad):
""" - ignora cancelados - toma último movimiento válido - deriva estado
"""
pass

⸻

🔄 FLUJO CORRECTO

1. Usuario registra movimiento
2. Sistema valida (no bloquea todo)
3. Marca inconsistencia si aplica
4. Guarda movimiento
5. Estado se recalcula

⸻

⚠️ REGLAS CRÍTICAS

- Nunca editar movimientos
- Nunca borrar movimientos
- Solo cancelar
- Correcciones = nuevos movimientos
- Historial siempre intacto

⸻

🚀 FUTURO (no implementar aún)

- GPS
- Notificaciones
- App móvil
- Integraciones externas

⸻

🎯 META

El sistema está listo cuando:

se puede saber dónde está cualquier unidad y entender su historial sin ambigüedad.

⸻
