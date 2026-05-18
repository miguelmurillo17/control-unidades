# Campos obligatorios en sub-inspecciones

## Regla general

Todas las sub-inspecciones permiten **guardar en cualquier momento** con datos parciales.
La validación de campos obligatorios solo aplica al intentar guardar con `completada = True`.

## Cómo declarar campos obligatorios

### Tipos de formulario con campos de texto/número (GENERAL, MEDIDAS_REMOLQUE, etc.)

Declara `required_for_completada` como atributo de clase en el formulario:

```python
class DetalleGeneralForm(forms.ModelForm):
    required_for_completada = ["id_caja", "linea", "placas", "marca_remolque", ...]
```

El helper `_validate_completada(sub_form, detalle_form)` en `views.py` lo lee automáticamente
y bloquea el guardado si alguno de esos campos está vacío cuando `completada=True`.

### Tipos checklist (CAJA, CAJA_VACIA, CINCO_PUNTOS, DIECINUEVE_PUNTOS, CANINA)

No necesitan `required_for_completada`. `_validate_checklist()` en `views.py` ya itera
dinámicamente sobre todos los campos del formulario e impide marcar como completada si
algún punto de revisión no tiene respuesta.

## Cómo agregar un campo obligatorio nuevo

1. Agregar el campo al modelo y aplicar la migración.
2. Agregarlo a `fields` en el formulario correspondiente.
3. Si es tipo texto/número: agregarlo a `required_for_completada` en el mismo formulario.
   Si es tipo checklist: no se requiere nada adicional.
4. En el template, agregar `data-req` al `<input>`/`<select>` o `data-req-radio="nombre"` al
   contenedor del grupo de radios. Esto activa la validación del lado del cliente.

## Por qué todos los campos del formulario son `required=False`

`_make_optional(form)` en `forms.py` pone `required=False` en todos los campos para que
`form.is_valid()` no bloquee los guardados parciales. La validación de obligatoriedad se
hace explícitamente después, condicionada al estado de `completada`.

## Archivos involucrados

| Archivo | Responsabilidad |
|---|---|
| `logistica/forms.py` | `required_for_completada` por formulario; `_make_optional()` |
| `logistica/views.py` | `_validate_completada()` (texto/número); `_validate_checklist()` (checklists) |
| `templates/logistica/inspecciones/_footer_sub.html` | JS cliente: bloquea checkbox si `[data-req]` o `[data-req-radio]` vacíos |
| `templates/logistica/inspecciones/_checklist_row.html` | `data-req-radio` por fila |
| `templates/logistica/inspecciones/_field.html` | `data-req` en inputs de texto |
| `templates/logistica/inspecciones/_field_select.html` | `data-req` en selects cuando `field.field.required` |
