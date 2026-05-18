from django import forms
from django.utils import timezone

from .models import (
    Unidad, Sucursal, Manifiesto, SubInspeccion, DetalleGeneral,
    DetalleCaja, DetalleCajaVacia, DetalleCincoPuntos, DetalleDiecinuevePuntos,
    DetalleCanina, DetalleMedidasRemolque, RegistroLlanta, Marca, MedidaLlanta,
)

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
        fields  = ["comentarios", "completada"]
        widgets = {"comentarios": forms.Textarea(attrs={"rows": 4})}


class DetalleGeneralForm(forms.ModelForm):
    required_for_completada = [
        "id_caja", "linea", "placas", "estado", "chofer",
        "id_tractor", "fianza", "numero_sello",
        "anio_remolque", "vin_remolque", "marca_remolque",
        "anio_contenedor", "vin_contenedor", "marca_contenedor",
    ]

    def __init__(self, *args, **kwargs):
        import datetime
        super().__init__(*args, **kwargs)
        self.fields["marca_remolque"].queryset   = Marca.objects.filter(aplica_remolque=True,   activo=True)
        self.fields["marca_contenedor"].queryset = Marca.objects.filter(aplica_contenedor=True, activo=True)
        self._año_max = datetime.date.today().year + 1
        for name in ("anio_remolque", "anio_contenedor"):
            self.fields[name].widget = forms.NumberInput(attrs={"min": 1950, "max": self._año_max})
        _make_optional(self)
        # marca_remolque/contenedor muestran label sin "(opcional)"
        self.fields["marca_remolque"].required   = True
        self.fields["marca_contenedor"].required = True

    def _validar_anio(self, field_name):
        valor = self.cleaned_data.get(field_name)
        if valor is not None and valor > self._año_max:
            raise forms.ValidationError(f"El año no puede ser mayor a {self._año_max}.")
        return valor

    def clean_anio_remolque(self):
        return self._validar_anio("anio_remolque")

    def clean_anio_contenedor(self):
        return self._validar_anio("anio_contenedor")

    class Meta:
        model  = DetalleGeneral
        fields = [
            "id_caja", "linea", "placas", "estado", "chofer", "id_tractor", "fianza",
            "anio_remolque", "vin_remolque", "marca_remolque",
            "anio_contenedor", "vin_contenedor", "marca_contenedor",
            "numero_sello",
        ]


def _make_optional(form_instance):
    for f in form_instance.fields.values():
        f.required = False


class DetalleCajaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _make_optional(self)

    class Meta:
        model  = DetalleCaja
        fields = [
            "remaches_de_carga", "manitas", "patines", "soqueteras",
            "manivelas", "golpes_y_rallones", "reflejantes", "molduras",
            "bisagras", "llantas", "receptor_electrico", "luz_lateral", "luz_trasera",
        ]


class DetalleCajaVaciaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _make_optional(self)

    class Meta:
        model  = DetalleCajaVacia
        fields = [
            "techo_libre_filtraciones", "libre_olores",
            "pisos_integros", "paredes_integros", "techos_integros",
            "bisagras", "mecanismos_de_cierre", "puertas_simetricas",
            "parches_y_reparaciones", "limpieza", "paredes_de_interior",
        ]


class DetalleDiecinuevePuntosForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _make_optional(self)

    class Meta:
        model  = DetalleDiecinuevePuntos
        fields = [
            "defensa", "llantas_y_rines", "piso_tractor", "tanque_gasolina",
            "interior_cabina", "tanques_de_aire", "chasis_y_quinta_rueda",
            "ejes_de_transmision", "tubo_de_escape", "motor",
            "base_del_remolque", "puertas_interiores", "pared_lateral_derecha",
            "techo_interno_y_externo", "pared_frontal", "pared_lateral_izquierda",
            "piso_interno", "eje_palanca_patin", "sistema_refrigeracion",
        ]


class DetalleCincoPuntosForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _make_optional(self)

    class Meta:
        model  = DetalleCincoPuntos
        fields = ["ver_sellos", "verificar_sello", "tirar_sello", "torcer_sello", "verificar_bisagra"]


class DetalleCaninaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _make_optional(self)

    class Meta:
        model  = DetalleCanina
        fields = ["aprobado"]


class DetalleMedidasRemolqueForm(forms.ModelForm):
    required_for_completada = ["largo", "ancho", "alto"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _make_optional(self)

    class Meta:
        model   = DetalleMedidasRemolque
        fields  = ["largo", "ancho", "alto"]
        widgets = {
            "largo": forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "m"}),
            "ancho": forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "m"}),
            "alto":  forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "m"}),
        }


class RegistroLlantaForm(forms.ModelForm):
    _VALIDADO = [("1", "Sí"), ("0", "No")]
    validado = forms.TypedChoiceField(
        choices=_VALIDADO,
        coerce=lambda x: x == "1",
        required=False,
        label="Validado",
        initial="0",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["marca"].queryset   = Marca.objects.filter(aplica_llanta=True, activo=True)
        self.fields["medida"].queryset  = MedidaLlanta.objects.all()
        self.fields["marca"].required   = False
        self.fields["medida"].required  = False
        # Represent the stored boolean as the string the TypedChoiceField expects
        if self.instance and self.instance.pk is not None:
            self.initial["validado"] = "1" if self.instance.validado else "0"
        else:
            self.initial["validado"] = "0"

    class Meta:
        model  = RegistroLlanta
        fields = ["cautin", "marca", "medida", "origen", "validado"]
