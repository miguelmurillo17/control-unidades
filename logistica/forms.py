from django import forms
from django.utils import timezone

from .models import Unidad, Sucursal, Manifiesto, SubInspeccion

def _manifiestos_activos():
    return (
        Manifiesto.objects
        .exclude(estado="CANCELADO")
        .select_related("sucursal_origen", "sucursal_destino")
        .order_by("-created_at")
    )

TIPO_CHOICES_CASETA = [
    ("", "— Selecciona —"),
    ("ENTRADA",        "Entrada"),
    ("SALIDA",         "Salida"),
    ("TALLER_ENTRADA", "Entrada a taller"),
    ("TALLER_SALIDA",  "Salida de taller"),
    ("INSPECCION",     "Inspección"),
]


class MovimientoForm(forms.Form):
    manifiesto = forms.ModelChoiceField(
        queryset=Manifiesto.objects.none(),
        empty_label="— Selecciona —",
        label="Manifiesto",
    )
    tractor = forms.ModelChoiceField(
        queryset=Unidad.objects.filter(activo=True, tipo="TRACTOR").order_by("numero_economico"),
        required=False,
        empty_label="— Ninguno —",
        label="Tractor",
    )
    remolque = forms.ModelChoiceField(
        queryset=Unidad.objects.filter(activo=True, tipo="REMOLQUE").order_by("numero_economico"),
        required=False,
        empty_label="— Ninguno —",
        label="Remolque",
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
        self.fields["manifiesto"].queryset = _manifiestos_activos()
        if not self.data:
            now = timezone.localtime(timezone.now())
            self.fields["fecha_hora_evento"].initial = now.strftime("%Y-%m-%dT%H:%M")

    def clean(self):
        cleaned = super().clean()
        tractor  = cleaned.get("tractor")
        remolque = cleaned.get("remolque")
        unidades = [u for u in [tractor, remolque] if u]
        if not unidades:
            raise forms.ValidationError("Selecciona al menos un tractor o remolque.")
        cleaned["unidades"] = unidades
        return cleaned


class ManifiestoForm(forms.Form):
    folio_hoja_viajera = forms.CharField(
        label="Folio hoja viajera",
        max_length=50,
    )
    tractor = forms.ModelChoiceField(
        queryset=Unidad.objects.filter(activo=True, tipo="TRACTOR").order_by("numero_economico"),
        required=False,
        empty_label="— Ninguno —",
        label="Tractor",
    )
    remolque = forms.ModelChoiceField(
        queryset=Unidad.objects.filter(activo=True, tipo="REMOLQUE").order_by("numero_economico"),
        required=False,
        empty_label="— Ninguno —",
        label="Remolque",
    )
    sucursal_origen = forms.ModelChoiceField(
        queryset=Sucursal.objects.filter(activo=True).order_by("nombre"),
        empty_label="— Selecciona —",
        label="Sucursal de origen",
    )
    sucursal_destino = forms.ModelChoiceField(
        queryset=Sucursal.objects.filter(activo=True).order_by("nombre"),
        empty_label="— Selecciona —",
        label="Sucursal de destino",
    )
    fecha_salida = forms.DateTimeField(
        label="Fecha y hora de salida",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    fecha_llegada_est = forms.DateTimeField(
        label="Llegada estimada",
        required=False,
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
            self.fields["fecha_salida"].initial = now.strftime("%Y-%m-%dT%H:%M")

    def clean(self):
        cleaned = super().clean()
        tractor  = cleaned.get("tractor")
        remolque = cleaned.get("remolque")
        unidades = [u for u in [tractor, remolque] if u]
        if not unidades:
            raise forms.ValidationError("Selecciona al menos un tractor o remolque.")
        origen  = cleaned.get("sucursal_origen")
        destino = cleaned.get("sucursal_destino")
        if origen and destino and origen == destino:
            raise forms.ValidationError("La sucursal de origen y destino no pueden ser la misma.")
        cleaned["unidades"] = unidades
        return cleaned


class SubInspeccionForm(forms.ModelForm):
    class Meta:
        model   = SubInspeccion
        fields  = ["resultado", "comentarios"]
        widgets = {"comentarios": forms.Textarea(attrs={"rows": 3})}
