from django import forms
from django.utils import timezone

from .models import Unidad, Sucursal

TIPO_CHOICES_CASETA = [
    ("", "— Selecciona —"),
    ("ENTRADA",        "Entrada"),
    ("SALIDA",         "Salida"),
    ("TALLER_ENTRADA", "Entrada a taller"),
    ("TALLER_SALIDA",  "Salida de taller"),
]


class MovimientoForm(forms.Form):
    unidades = forms.ModelMultipleChoiceField(
        queryset=Unidad.objects.filter(activo=True).order_by("tipo", "numero_economico"),
        widget=forms.CheckboxSelectMultiple,
        label="Unidades",
    )
    tipo = forms.ChoiceField(choices=TIPO_CHOICES_CASETA, label="Tipo de movimiento")
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.filter(activo=True).order_by("nombre"),
        empty_label="— Selecciona —",
        label="Sucursal",
    )
    fecha_hora_evento = forms.DateTimeField(
        label="Fecha y hora del evento",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data:
            now = timezone.localtime(timezone.now())
            self.fields["fecha_hora_evento"].initial = now.strftime("%Y-%m-%dT%H:%M")

    def clean_unidades(self):
        unidades = self.cleaned_data.get("unidades")
        if not unidades:
            raise forms.ValidationError("Selecciona al menos una unidad.")
        if len(unidades) > 3:
            raise forms.ValidationError("No puedes registrar más de 3 unidades por movimiento.")
        return unidades
