# Sistema de Control y Trazabilidad de Unidades

Sistema web para monitorear unidades logísticas (tractores y remolques) mediante el registro de movimientos e inspecciones realizadas en sucursales.

> **Alcance:** El sistema está orientado a operación real en patios/casetas. **No** administra mercancía ni embarques.

---

## Objetivo

Responder en todo momento: **¿Dónde está cada unidad y cuál fue su último movimiento?**

El sistema debe permitir:

- Registrar entradas y salidas de unidades
- Registrar inspecciones operativas
- Mantener estado actual de unidades
- Generar evidencia en PDF
- Consultar historial completo
- Visualizar estado por sucursal

---

## Principios de Diseño

| # | Principio | Descripción |
|---|-----------|-------------|
| 1 | **Operación primero** | Captura rápida (<1 min), interfaces simples, evitar fricción en caseta/patio |
| 2 | **Trazabilidad completa** | Nunca editar ni borrar movimientos; todo cambio se registra como nuevo evento |
| 3 | **Registrar realidad** | Permitir guardar aunque haya errores; marcar inconsistencias en lugar de bloquear |
| 4 | **Historial inmutable** | El pasado no se modifica; solo se agregan eventos |
| 5 | **Simplicidad** | No optimizar rutas, no automatizar decisiones; solo registrar y mostrar |

---

## Modelo de Datos

### `Unidad`

Representa un tractor o remolque.

```python
class Unidad:
    numero_economico: str       # Identificador único
    tipo: str                   # "TRACTOR" | "REMOLQUE"
    sucursal_actual: str        # Derivada del último movimiento válido
    estado_actual: str          # Derivado del último movimiento válido
```

### `Movimiento` _(entidad principal)_

Representa cualquier evento que ocurre a una unidad.

```python
class Movimiento:
    unidad: Unidad
    tipo_movimiento: str        # "ENTRADA" | "SALIDA" | "TALLER_ENTRADA" | "TALLER_SALIDA" | "CORRECCION"
    sucursal: str
    fecha_hora_evento: datetime
    fecha_hora_registro: datetime
    usuario: str
    observaciones: str
    inconsistente: bool         # True si rompe la lógica esperada
    cancelado: bool             # True si fue anulado lógicamente
    referencia_movimiento: int  # Opcional; apunta al movimiento original (usado en CORRECCION)
```

### `Inspeccion`

Checklist asociado a un movimiento.

```python
class Inspeccion:
    movimiento: Movimiento
    resultado_general: str
    observaciones: str
```

### `DetalleInspeccion`

```python
class DetalleInspeccion:
    inspeccion: Inspeccion
    punto_revision: str
    resultado: str
    comentario: str
```

---

## Reglas de Negocio

### Inmutabilidad de movimientos

- Los movimientos **nunca** se editan ni eliminan
- Solo pueden marcarse como cancelados: `cancelado = True`
- La cancelación es lógica y no borra el registro del historial

### Correcciones

Los errores se corrigen creando un nuevo movimiento:

```python
# ✅ CORRECTO
Movimiento(tipo_movimiento="CORRECCION", referencia_movimiento=id_original)

# ❌ NUNCA hacer esto
movimiento_original.campo = nuevo_valor
```

### Cálculo del estado actual

```python
def get_estado_actual(unidad):
    movimientos = Movimiento.objects.filter(
        unidad=unidad,
        cancelado=False       # 1. Ignorar cancelados
    ).order_by("-fecha_hora_evento")

    ultimo = movimientos.first()  # 2. Tomar el más reciente
    return derivar_estado(ultimo) # 3. Derivar estado
```

> **Nunca** depender de un campo editable para calcular el estado.

### Inconsistencias

Cuando un movimiento rompe la lógica esperada (ej. entrada sin salida previa), se guarda con `inconsistente = True`. **El sistema no bloquea el guardado.**

---

## Comportamiento de UX ante Inconsistencias

Mostrar advertencia y permitir continuar:

```
⚠️  Esta unidad no tiene salida previa registrada.
    Puedes continuar y corregir posteriormente.
    [Cancelar]  [Continuar de todas formas]
```

---

## PDFs de Inspección

Cada PDF generado debe:

- Tener **folio único**
- Incluir unidad, fecha y sucursal
- Servir como **evidencia operativa**
- Generarse **desde el sistema** (no con herramientas externas)

---

## Roles

| Rol | Acceso |
|-----|--------|
| `CASETA` | Captura de movimientos e inspecciones |
| `TRAFICO` | Consulta de historial y estado |
| `ADMIN` | Configuración del sistema |

> No implementar permisos complejos más allá de estos tres roles.

---

## Stack Tecnológico

El sistema debe construirse con un stack orientado a **simplicidad, estabilidad y fácil despliegue en Ubuntu Server**.

| Capa | Tecnología | Notas |
|------|-----------|-------|
| **Backend** | Django + Python 3.11+ | Django REST Framework solo si se requiere API |
| **Base de datos** | PostgreSQL | SQLite permitido únicamente en desarrollo local |
| **Frontend** | Django Templates + HTMX | JavaScript mínimo, solo cuando sea necesario |
| **Estilos** | CSS simple / Tailwind CSS (opcional) | Priorizar funcionalidad sobre diseño visual |
| **Generación de PDF** | WeasyPrint (preferido) | Alternativa: wkhtmltopdf |
| **Autenticación** | `AbstractUser` nativo de Django | Sin librerías externas de auth |
| **Servidor de app** | Gunicorn | Solo producción |
| **Reverse proxy** | Nginx | Sirve archivos estáticos y hace proxy a Gunicorn |
| **SO objetivo** | Ubuntu Server LTS | On-premise o VPS (DigitalOcean, AWS, etc.) |
| **Archivos estáticos** | `collectstatic` + Nginx | No usar whitenoise en producción |
| **Configuración** | Variables de entorno via `python-decouple` | Archivo `.env` en raíz del proyecto |
| **Entorno virtual** | `venv` | Obligatorio |
| **Procesos (prod)** | `systemd` o `supervisor` | Para mantener Gunicorn activo |

### Filosofía Técnica

> El sistema debe poder instalarse en un servidor Ubuntu limpio, con pasos claros y sin dependencias complejas.

### Exclusiones del Stack — Copilot NO debe introducir

- Frameworks frontend complejos (React, Angular, Vue)
- Dependencias innecesarias o difíciles de configurar en Linux
- Arquitectura de microservicios
- Colas de tareas (Celery, Redis) en el MVP
- Servicios externos obligatorios para el funcionamiento base

---

## Exclusiones Funcionales — Lo que Copilot NO debe generar

- GPS o tracking en tiempo real
- Integraciones con sistemas externos
- Aplicación móvil
- Notificaciones automáticas
- Lógica de optimización logística
- Asignación de viajes o workflows complejos

---

## Prioridad de Desarrollo

```
1. Modelo de datos correcto
2. Movimientos robustos
3. Consistencia de estado
4. Flujo de captura rápido
5. Visualización
6. Reportes
```

---

## Criterio de Éxito del MVP

> El sistema está listo cuando se puede identificar la **última ubicación** de cualquier unidad y consultar su **historial completo** sin inconsistencias críticas.

---

## Filosofía

> El sistema debe adaptarse a la operación real, no obligar a la operación a adaptarse al sistema.
