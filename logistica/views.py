from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from django.db.models import Count, Q

from django.forms import inlineformset_factory

from .forms import (
    MovimientoForm, ManifiestoForm, SubInspeccionForm, DetalleGeneralForm,
    DetalleCajaForm, DetalleCajaVaciaForm, DetalleCincoPuntosForm,
    DetalleDiecinuevePuntosForm, DetalleCaninaForm, DetalleMedidasRemolqueForm,
    RegistroLlantaForm,
)
from .models import (
    DetalleGeneral, DetalleCaja, DetalleCajaVacia, DetalleCincoPuntos,
    DetalleDiecinuevePuntos, DetalleCanina, DetalleMedidasRemolque,
    RegistroLlanta, PosicionLlanta, FotoSubInspeccion, ConfiguracionInspeccion,
    Inspeccion, Manifiesto, Movimiento, SubInspeccion, Sucursal, Unidad, UnidadManifiesto,
)
from .services import detectar_inconsistencias, crear_movimiento


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.rol == "ADMIN"


class SucursalListView(AdminRequiredMixin, ListView):
    model = Sucursal
    template_name = "logistica/sucursales/list.html"
    context_object_name = "sucursales"
    ordering = ["nombre"]


class SucursalCreateView(AdminRequiredMixin, CreateView):
    model = Sucursal
    template_name = "logistica/sucursales/form.html"
    fields = ["nombre", "ciudad", "tipo", "activo"]
    success_url = reverse_lazy("sucursales:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva sucursal"
        ctx["accion"] = "Crear"
        return ctx


class SucursalUpdateView(AdminRequiredMixin, UpdateView):
    model = Sucursal
    template_name = "logistica/sucursales/form.html"
    fields = ["nombre", "ciudad", "tipo", "activo"]
    success_url = reverse_lazy("sucursales:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar sucursal"
        ctx["accion"] = "Guardar cambios"
        return ctx


class SucursalDeleteView(AdminRequiredMixin, DeleteView):
    model = Sucursal
    template_name = "logistica/sucursales/confirm_delete.html"
    success_url = reverse_lazy("sucursales:list")


class UnidadListView(AdminRequiredMixin, ListView):
    model = Unidad
    template_name = "logistica/unidades/list.html"
    context_object_name = "unidades"
    ordering = ["numero_economico"]


class UnidadCreateView(AdminRequiredMixin, CreateView):
    model = Unidad
    template_name = "logistica/unidades/form.html"
    fields = ["numero_economico", "tipo", "sucursal_actual", "activo"]
    success_url = reverse_lazy("unidades:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva unidad"
        ctx["accion"] = "Crear"
        return ctx


class UnidadUpdateView(AdminRequiredMixin, UpdateView):
    model = Unidad
    template_name = "logistica/unidades/form.html"
    fields = ["numero_economico", "tipo", "sucursal_actual", "activo"]
    success_url = reverse_lazy("unidades:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar unidad"
        ctx["accion"] = "Guardar cambios"
        return ctx


class UnidadDeleteView(AdminRequiredMixin, DeleteView):
    model = Unidad
    template_name = "logistica/unidades/confirm_delete.html"
    success_url = reverse_lazy("unidades:list")


@login_required
def mis_registros(request):
    if request.user.rol != "CASETA":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    movimientos = (
        Movimiento.objects
        .filter(usuario=request.user)
        .prefetch_related("unidad_movimientos__unidad", "sucursal")
        .order_by("-fecha_hora_evento")
    )
    return render(request, "logistica/movimientos/mis_registros.html", {
        "movimientos": movimientos,
    })


@login_required
def registrar_movimiento(request):
    if request.user.rol != "CASETA":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    movimiento_guardado = None

    if request.method == "POST":
        form = MovimientoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            confirmar = request.POST.get("confirmar") == "1"

            advertencias = detectar_inconsistencias(data["unidades"], data["tipo"])

            if advertencias and not confirmar:
                return render(request, "logistica/movimientos/form.html", {
                    "form": form,
                    "advertencias": advertencias,
                })

            movimiento_guardado = crear_movimiento(data, request.user)
            if movimiento_guardado.tipo == "INSPECCION":
                return redirect("inspeccion_detalle", pk=movimiento_guardado.inspeccion.pk)
            form = MovimientoForm()
    else:
        form = MovimientoForm()

    return render(request, "logistica/movimientos/form.html", {
        "form": form,
        "movimiento_guardado": movimiento_guardado,
    })


@login_required
def mis_inspecciones(request):
    if request.user.rol not in ("CASETA", "ADMIN"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    inspecciones = (
        Inspeccion.objects
        .filter(movimiento__usuario=request.user)
        .select_related("movimiento__manifiesto__sucursal_origen", "movimiento__manifiesto__sucursal_destino")
        .annotate(
            total_subs=Count("sub_inspecciones"),
            completadas_subs=Count("sub_inspecciones", filter=Q(sub_inspecciones__completada=True)),
        )
        .order_by("-created_at")
    )
    return render(request, "logistica/inspecciones/mis_inspecciones.html", {
        "inspecciones": inspecciones,
    })


@login_required
def inspeccion_detalle(request, pk):
    if request.user.rol not in ("CASETA", "ADMIN"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    inspeccion = get_object_or_404(
        Inspeccion.objects.select_related(
            "movimiento__sucursal",
            "movimiento__manifiesto__sucursal_origen",
            "movimiento__manifiesto__sucursal_destino",
        ).prefetch_related("sub_inspecciones"),
        pk=pk,
    )
    sub_inspecciones = inspeccion.sub_inspecciones.all()
    completadas = sum(1 for s in sub_inspecciones if s.completada)
    total       = len(sub_inspecciones)

    return render(request, "logistica/inspecciones/detalle.html", {
        "inspeccion":     inspeccion,
        "sub_inspecciones": sub_inspecciones,
        "completadas":    completadas,
        "total":          total,
        "porcentaje":     int(completadas / total * 100) if total else 0,
    })


# Tipos con checklist SI/NO donde "algún NO" exige comentarios ≥ 10 chars
_CHECKLIST_TIPOS = {"CAJA", "CAJA_VACIA", "CINCO_PUNTOS", "DIECINUEVE_PUNTOS", "CANINA"}


def _get_fotos_ctx(sub_inspeccion):
    max_fotos = ConfiguracionInspeccion.get().max_fotos
    fotos     = list(sub_inspeccion.fotos.all())
    return {"fotos": fotos, "max_fotos": max_fotos, "puede_agregar_foto": len(fotos) < max_fotos}


def _save_fotos(request, sub_inspeccion):
    max_fotos = ConfiguracionInspeccion.get().max_fotos
    existing  = sub_inspeccion.fotos.count()
    slots     = max(0, max_fotos - existing)
    for f in request.FILES.getlist("fotos")[:slots]:
        FotoSubInspeccion.objects.create(sub_inspeccion=sub_inspeccion, imagen=f)


def _apply_completada(sub):
    from django.utils import timezone
    if sub.completada:
        if not sub.fecha_hora_fin:
            sub.fecha_hora_fin = timezone.now()
    else:
        sub.fecha_hora_fin = None


def _validate_completada(sub_form, detalle_form):
    """Blocks saving completada=True when required_for_completada fields are empty.
    For checklist types this is handled by _validate_checklist instead."""
    if not sub_form.cleaned_data.get("completada"):
        return True
    campos = getattr(detalle_form, "required_for_completada", None)
    if campos is None:
        return True
    vacios = [k for k in campos if not detalle_form.cleaned_data.get(k)]
    if vacios:
        sub_form.add_error("completada", "Completa todos los campos obligatorios antes de marcar como completada.")
        return False
    return True


def _validate_checklist(sub_form, detalle_form, tipo):
    """Returns True if validation passes; otherwise adds errors to sub_form and returns False."""
    if tipo not in _CHECKLIST_TIPOS:
        return True
    cleaned    = detalle_form.cleaned_data
    completada = sub_form.cleaned_data.get("completada", False)
    # Si se marca completada, todos los puntos deben estar respondidos
    if completada:
        vacios = [k for k, v in cleaned.items() if isinstance(v, str) and v == ""]
        if vacios:
            sub_form.add_error(None, "Completa todos los puntos de revisión antes de marcar como completada.")
            return False
    # Si algún punto es "NO", comentarios es obligatorio (mín. 10 chars)
    tiene_mal = any(v == "NO" for v in cleaned.values() if isinstance(v, str))
    if tiene_mal:
        comentarios = (sub_form.cleaned_data.get("comentarios") or "").strip()
        if len(comentarios) < 10:
            sub_form.add_error("comentarios", "Requerido (mín. 10 caracteres) cuando hay puntos marcados como Mal.")
            return False
    return True


def _marcar_completada_si_aplica(inspeccion):
    todas = inspeccion.sub_inspecciones.all()
    if all(s.completada for s in todas):
        inspeccion.estado = "COMPLETADA"
        inspeccion.save(update_fields=["estado"])


@login_required
def sub_inspeccion_form(request, pk, sub_pk):
    if request.user.rol not in ("CASETA", "ADMIN"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    inspeccion     = get_object_or_404(Inspeccion, pk=pk)
    sub_inspeccion = get_object_or_404(SubInspeccion, pk=sub_pk, inspeccion=inspeccion)

    # Registrar inicio automáticamente al abrir por primera vez
    if not sub_inspeccion.fecha_hora_inicio:
        from django.utils import timezone
        sub_inspeccion.fecha_hora_inicio = timezone.now()
        sub_inspeccion.save(update_fields=["fecha_hora_inicio"])

    if sub_inspeccion.tipo == "GENERAL":
        return _sub_form_general(request, inspeccion, sub_inspeccion)
    if sub_inspeccion.tipo == "CAJA":
        return _sub_form_caja(request, inspeccion, sub_inspeccion)
    if sub_inspeccion.tipo == "CAJA_VACIA":
        return _sub_form_caja_vacia(request, inspeccion, sub_inspeccion)
    if sub_inspeccion.tipo == "DIECINUEVE_PUNTOS":
        return _sub_form_diecinueve_puntos(request, inspeccion, sub_inspeccion)
    if sub_inspeccion.tipo == "LLANTAS":
        return _sub_form_llantas(request, inspeccion, sub_inspeccion)
    if sub_inspeccion.tipo == "CINCO_PUNTOS":
        return _sub_form_cinco_puntos(request, inspeccion, sub_inspeccion)
    if sub_inspeccion.tipo == "CANINA":
        return _sub_form_canina(request, inspeccion, sub_inspeccion)
    if sub_inspeccion.tipo == "MEDIDAS_REMOLQUE":
        return _sub_form_medidas_remolque(request, inspeccion, sub_inspeccion)

    # Formulario genérico para tipos aún no implementados
    if request.method == "POST":
        form = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        if form.is_valid():
            sub = form.save(commit=False)
            _apply_completada(sub)
            sub.save()
            _save_fotos(request, sub_inspeccion)
            _marcar_completada_si_aplica(inspeccion)
            return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        form = SubInspeccionForm(instance=sub_inspeccion)

    return render(request, "logistica/inspecciones/sub_form.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "form":           form,
        **_get_fotos_ctx(sub_inspeccion),
    })


def _sub_form_general(request, inspeccion, sub_inspeccion):
    detalle = DetalleGeneral.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form    = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleGeneralForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            ok = _validate_completada(sub_form, detalle_form)
            if ok:
                sub = sub_form.save(commit=False)
                _apply_completada(sub)
                sub.save()
                det = detalle_form.save(commit=False)
                det.sub_inspeccion = sub_inspeccion
                det.save()
                _save_fotos(request, sub_inspeccion)
                _marcar_completada_si_aplica(inspeccion)
                return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        sub_form     = SubInspeccionForm(instance=sub_inspeccion)
        detalle_form = DetalleGeneralForm(instance=detalle)

    return render(request, "logistica/inspecciones/sub_general.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "sub_form":       sub_form,
        "detalle_form":   detalle_form,
        **_get_fotos_ctx(sub_inspeccion),
    })


def _sub_form_caja(request, inspeccion, sub_inspeccion):
    detalle = DetalleCaja.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form     = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleCajaForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            if _validate_checklist(sub_form, detalle_form, sub_inspeccion.tipo):
                sub = sub_form.save(commit=False)
                _apply_completada(sub)
                sub.save()
                det = detalle_form.save(commit=False)
                det.sub_inspeccion = sub_inspeccion
                det.save()
                _save_fotos(request, sub_inspeccion)
                _marcar_completada_si_aplica(inspeccion)
                return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        sub_form     = SubInspeccionForm(instance=sub_inspeccion)
        detalle_form = DetalleCajaForm(instance=detalle)

    return render(request, "logistica/inspecciones/sub_caja.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "sub_form":       sub_form,
        "detalle_form":   detalle_form,
        **_get_fotos_ctx(sub_inspeccion),
    })


def _sub_form_caja_vacia(request, inspeccion, sub_inspeccion):
    detalle = DetalleCajaVacia.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form     = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleCajaVaciaForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            if _validate_checklist(sub_form, detalle_form, sub_inspeccion.tipo):
                sub = sub_form.save(commit=False)
                _apply_completada(sub)
                sub.save()
                det = detalle_form.save(commit=False)
                det.sub_inspeccion = sub_inspeccion
                det.save()
                _save_fotos(request, sub_inspeccion)
                _marcar_completada_si_aplica(inspeccion)
                return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        sub_form     = SubInspeccionForm(instance=sub_inspeccion)
        detalle_form = DetalleCajaVaciaForm(instance=detalle)

    return render(request, "logistica/inspecciones/sub_caja_vacia.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "sub_form":       sub_form,
        "detalle_form":   detalle_form,
        **_get_fotos_ctx(sub_inspeccion),
    })


_LlantaFormSet = inlineformset_factory(
    SubInspeccion, RegistroLlanta,
    form=RegistroLlantaForm,
    extra=0,
    can_delete=False,
)


def _sub_form_llantas(request, inspeccion, sub_inspeccion):
    # Pre-create one RegistroLlanta per required position (idempotent)
    for pos in PosicionLlanta.objects.filter(requerir_en_inspeccion=True):
        RegistroLlanta.objects.get_or_create(sub_inspeccion=sub_inspeccion, posicion=pos)

    qs = RegistroLlanta.objects.filter(sub_inspeccion=sub_inspeccion).order_by("posicion__nombre")

    if request.method == "POST":
        sub_form = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        formset  = _LlantaFormSet(request.POST, instance=sub_inspeccion, queryset=qs)
        if sub_form.is_valid() and formset.is_valid():
            sub = sub_form.save(commit=False)
            _apply_completada(sub)
            sub.save()
            formset.save()
            _save_fotos(request, sub_inspeccion)
            _marcar_completada_si_aplica(inspeccion)
            return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        sub_form = SubInspeccionForm(instance=sub_inspeccion)
        formset  = _LlantaFormSet(instance=sub_inspeccion, queryset=qs)

    return render(request, "logistica/inspecciones/sub_llantas.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "sub_form":       sub_form,
        "formset":        formset,
        **_get_fotos_ctx(sub_inspeccion),
    })


def _sub_form_diecinueve_puntos(request, inspeccion, sub_inspeccion):
    detalle = DetalleDiecinuevePuntos.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form     = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleDiecinuevePuntosForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            if _validate_checklist(sub_form, detalle_form, sub_inspeccion.tipo):
                sub = sub_form.save(commit=False)
                _apply_completada(sub)
                sub.save()
                det = detalle_form.save(commit=False)
                det.sub_inspeccion = sub_inspeccion
                det.save()
                _save_fotos(request, sub_inspeccion)
                _marcar_completada_si_aplica(inspeccion)
                return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        sub_form     = SubInspeccionForm(instance=sub_inspeccion)
        detalle_form = DetalleDiecinuevePuntosForm(instance=detalle)

    return render(request, "logistica/inspecciones/sub_diecinueve_puntos.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "sub_form":       sub_form,
        "detalle_form":   detalle_form,
        **_get_fotos_ctx(sub_inspeccion),
    })


def _sub_form_cinco_puntos(request, inspeccion, sub_inspeccion):
    detalle = DetalleCincoPuntos.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form     = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleCincoPuntosForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            if _validate_checklist(sub_form, detalle_form, sub_inspeccion.tipo):
                sub = sub_form.save(commit=False)
                _apply_completada(sub)
                sub.save()
                det = detalle_form.save(commit=False)
                det.sub_inspeccion = sub_inspeccion
                det.save()
                _save_fotos(request, sub_inspeccion)
                _marcar_completada_si_aplica(inspeccion)
                return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        sub_form     = SubInspeccionForm(instance=sub_inspeccion)
        detalle_form = DetalleCincoPuntosForm(instance=detalle)

    return render(request, "logistica/inspecciones/sub_cinco_puntos.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "sub_form":       sub_form,
        "detalle_form":   detalle_form,
        **_get_fotos_ctx(sub_inspeccion),
    })


def _sub_form_canina(request, inspeccion, sub_inspeccion):
    detalle = DetalleCanina.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form     = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleCaninaForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            if _validate_checklist(sub_form, detalle_form, sub_inspeccion.tipo):
                sub = sub_form.save(commit=False)
                _apply_completada(sub)
                sub.save()
                det = detalle_form.save(commit=False)
                det.sub_inspeccion = sub_inspeccion
                det.save()
                _save_fotos(request, sub_inspeccion)
                _marcar_completada_si_aplica(inspeccion)
                return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        sub_form     = SubInspeccionForm(instance=sub_inspeccion)
        detalle_form = DetalleCaninaForm(instance=detalle)

    return render(request, "logistica/inspecciones/sub_canina.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "sub_form":       sub_form,
        "detalle_form":   detalle_form,
        **_get_fotos_ctx(sub_inspeccion),
    })


def _sub_form_medidas_remolque(request, inspeccion, sub_inspeccion):
    detalle = DetalleMedidasRemolque.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form     = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleMedidasRemolqueForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            ok = _validate_completada(sub_form, detalle_form)
            if ok:
                sub = sub_form.save(commit=False)
                _apply_completada(sub)
                sub.save()
                det = detalle_form.save(commit=False)
                det.sub_inspeccion = sub_inspeccion
                det.save()
                _save_fotos(request, sub_inspeccion)
                _marcar_completada_si_aplica(inspeccion)
                return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        sub_form     = SubInspeccionForm(instance=sub_inspeccion)
        detalle_form = DetalleMedidasRemolqueForm(instance=detalle)

    return render(request, "logistica/inspecciones/sub_medidas_remolque.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "sub_form":       sub_form,
        "detalle_form":   detalle_form,
        **_get_fotos_ctx(sub_inspeccion),
    })


@login_required
def manifiestos_list(request):
    if request.user.rol != "PLANEACION":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    manifiestos = (
        Manifiesto.objects
        .exclude(estado="CANCELADO")
        .select_related("sucursal_origen", "sucursal_destino", "usuario")
        .prefetch_related("unidad_manifiestos__unidad")
        .order_by("-created_at")
    )
    return render(request, "logistica/manifiestos/list.html", {"manifiestos": manifiestos})


@login_required
def registrar_manifiesto(request):
    if request.user.rol != "PLANEACION":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    manifiesto_guardado = None

    if request.method == "POST":
        form = ManifiestoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            manifiesto = Manifiesto.objects.create(
                folio_hoja_viajera=data["folio_hoja_viajera"],
                sucursal_origen=data["sucursal_origen"],
                sucursal_destino=data["sucursal_destino"],
                fecha_salida=data["fecha_salida"],
                fecha_llegada_est=data.get("fecha_llegada_est"),
                usuario=request.user,
                observaciones=data.get("observaciones", ""),
            )
            for unidad in data["unidades"]:
                UnidadManifiesto.objects.create(manifiesto=manifiesto, unidad=unidad)
            manifiesto_guardado = manifiesto
            form = ManifiestoForm()
    else:
        form = ManifiestoForm()

    return render(request, "logistica/manifiestos/form.html", {
        "form": form,
        "manifiesto_guardado": manifiesto_guardado,
        "active_nav": "nuevo_manifiesto",
    })


@login_required
def editar_manifiesto(request, pk):
    if request.user.rol != "PLANEACION":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    manifiesto = get_object_or_404(Manifiesto, pk=pk)
    tractor  = manifiesto.unidades.filter(tipo="TRACTOR").first()
    remolque = manifiesto.unidades.filter(tipo="REMOLQUE").first()

    if request.method == "POST":
        form = ManifiestoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            manifiesto.folio_hoja_viajera = data["folio_hoja_viajera"]
            manifiesto.sucursal_origen    = data["sucursal_origen"]
            manifiesto.sucursal_destino   = data["sucursal_destino"]
            manifiesto.fecha_salida       = data["fecha_salida"]
            manifiesto.fecha_llegada_est  = data.get("fecha_llegada_est")
            manifiesto.observaciones      = data.get("observaciones", "")
            manifiesto.save()
            manifiesto.unidad_manifiestos.all().delete()
            for unidad in data["unidades"]:
                UnidadManifiesto.objects.create(manifiesto=manifiesto, unidad=unidad)
            return redirect("manifiestos:list")
    else:
        def fmt(dt):
            return dt.strftime("%Y-%m-%dT%H:%M") if dt else ""

        form = ManifiestoForm(initial={
            "folio_hoja_viajera": manifiesto.folio_hoja_viajera,
            "sucursal_origen":    manifiesto.sucursal_origen_id,
            "sucursal_destino":   manifiesto.sucursal_destino_id,
            "tractor":            tractor.pk  if tractor  else None,
            "remolque":           remolque.pk if remolque else None,
            "fecha_salida":       fmt(manifiesto.fecha_salida),
            "fecha_llegada_est":  fmt(manifiesto.fecha_llegada_est),
            "observaciones":      manifiesto.observaciones,
        })

    return render(request, "logistica/manifiestos/form.html", {
        "form": form,
        "manifiesto": manifiesto,
        "active_nav": "manifiestos",
    })
