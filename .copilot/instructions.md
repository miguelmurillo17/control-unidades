Proyecto

Sistema de Control y Trazabilidad de Unidades

Sistema web para monitorear unidades logísticas (tractores y remolques) mediante el registro de movimientos e inspecciones realizadas en sucursales.

El sistema está orientado a operación real en patios/casetas.
No administra mercancía ni embarques.

⸻

Objetivo del Sistema

Responder en todo momento:

¿Dónde está cada unidad y cuál fue su último movimiento?

El sistema debe permitir:

- Registrar entradas y salidas de unidades
- Registrar inspecciones operativas
- Mantener estado actual de unidades
- Generar evidencia en PDF
- Consultar historial completo
- Visualizar estado por sucursal

⸻

Principios de Diseño

1. Operación primero

- Captura rápida (menos de 1 minuto)
- Interfaces simples
- Evitar fricción en caseta/patio

2. Trazabilidad completa

- Nunca editar movimientos
- Nunca borrar movimientos
- Todo cambio se registra como nuevo evento

3. Registrar realidad > forzar reglas

- Permitir registrar aunque haya errores
- Marcar inconsistencias en lugar de bloquear

4. Historial inmutable

- El pasado no se modifica
- Solo se agregan eventos

5. Simplicidad

- No optimizar rutas
- No automatizar decisiones
- Solo registrar y mostrar

⸻

Concepto Central

El sistema se basa en:

Eventos (Movimientos)

Todo lo que sucede a una unidad es un evento.

⸻

Modelo Conceptual

Unidad

Representa tractor o remolque.

Campos clave:

- numero_economico
- tipo (TRACTOR / REMOLQUE)
- sucursal_actual (derivada)
- estado_actual (derivado)

⸻

Movimiento (Entidad principal)

Representa eventos como:

- ENTRADA
- SALIDA
- TALLER_ENTRADA
- TALLER_SALIDA
- CORRECCION

Campos clave:

- unidad
- tipo_movimiento
- sucursal
- fecha_hora_evento
- fecha_hora_registro
- usuario
- observaciones
- inconsistente (bool)
- cancelado (bool)
- referencia_movimiento (opcional)

⸻

Inspeccion

Checklist asociado a un movimiento.

- movimiento
- resultado_general
- observaciones

⸻

DetalleInspeccion

- inspeccion
- punto_revision
- resultado
- comentario

⸻

Reglas Clave

Movimientos

- Son inmutables
- No se editan
- No se eliminan
- Solo se pueden cancelar (cancelado = True)

⸻

Correcciones

Los errores se manejan creando nuevos movimientos:

- tipo = CORRECCION
- referencia al movimiento original

Nunca modificar el movimiento original.

⸻

Cancelación lógica

movimiento.cancelado = True

- No afecta historial
- No se usa para calcular estado

⸻

Estado actual

Se calcula:

1. Ignorar movimientos cancelados
2. Tomar el último movimiento válido
3. Derivar estado

Nunca depender de un campo editable.

⸻

Inconsistencias

Cuando un movimiento rompe lógica esperada:

movimiento.inconsistente = True

Ejemplo:

- entrada sin salida previa
- cambios fuera de secuencia

El sistema debe permitir guardar.

⸻

UX / Comportamiento

Cuando haya inconsistencias:

- Mostrar advertencia
- Permitir continuar

Ejemplo:

⚠️ Esta unidad no tiene salida previa registrada
Puedes continuar y corregir posteriormente

⸻

PDFs

Los PDFs de inspección deben:

- tener folio único
- incluir unidad, fecha, sucursal
- ser evidencia operativa
- generarse desde el sistema (no externo)

⸻

Roles

Solo tres roles:

- CASETA → captura
- TRAFICO → consulta
- ADMIN → configuración

No implementar permisos complejos.

⸻

Lo que NO debe generar Copilot

- GPS o tracking en tiempo real
- Integraciones externas
- App móvil
- Notificaciones automáticas
- Lógica de optimización logística
- Asignación de viajes
- Workflows complejos

⸻

Enfoque de Desarrollo

Orden de prioridad:

1. Modelo de datos correcto
2. Movimientos robustos
3. Consistencia de estado
4. Flujo de captura rápido
5. Visualización
6. Reportes

⸻

Meta del MVP

El sistema está listo cuando:

Se puede identificar la última ubicación de cualquier unidad y consultar su historial sin inconsistencias críticas.

⸻

Filosofía del Sistema

El sistema debe adaptarse a la operación real, no obligar a la operación a adaptarse al sistema.

⸻
