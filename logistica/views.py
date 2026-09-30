import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
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
    Inspeccion, Linea, Manifiesto, Movimiento, SubInspeccion, Sucursal, Unidad, UnidadManifiesto,
    TIPO_SUB_INSPECCION,
)
from .services import detectar_inconsistencias, crear_movimiento


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.rol == "ADMIN"


class LineaListView(AdminRequiredMixin, ListView):
    model = Linea
    template_name = "logistica/lineas/list.html"
    context_object_name = "lineas"
    ordering = ["clave"]


class LineaCreateView(AdminRequiredMixin, CreateView):
    model = Linea
    template_name = "logistica/lineas/form.html"
    fields = ["nombre", "clave", "tipo_linea", "activo"]
    success_url = reverse_lazy("lineas:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva línea"
        ctx["accion"] = "Crear"
        return ctx


class LineaUpdateView(AdminRequiredMixin, UpdateView):
    model = Linea
    template_name = "logistica/lineas/form.html"
    fields = ["nombre", "clave", "tipo_linea", "activo"]
    success_url = reverse_lazy("lineas:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar línea"
        ctx["accion"] = "Guardar cambios"
        return ctx


class LineaDeleteView(AdminRequiredMixin, DeleteView):
    model = Linea
    template_name = "logistica/lineas/confirm_delete.html"
    success_url = reverse_lazy("lineas:list")


class SucursalListView(AdminRequiredMixin, ListView):
    model = Sucursal
    template_name = "logistica/sucursales/list.html"
    context_object_name = "sucursales"
    ordering = ["nombre"]


class SucursalCreateView(AdminRequiredMixin, CreateView):
    model = Sucursal
    template_name = "logistica/sucursales/form.html"
    fields = ["nombre", "codigo", "tipo", "activo"]
    success_url = reverse_lazy("sucursales:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva sucursal"
        ctx["accion"] = "Crear"
        return ctx


class SucursalUpdateView(AdminRequiredMixin, UpdateView):
    model = Sucursal
    template_name = "logistica/sucursales/form.html"
    fields = ["nombre", "codigo", "tipo", "activo"]
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
    fields = ["numero_economico", "vin", "linea", "tipo", "sucursal_actual", "activo"]
    success_url = reverse_lazy("unidades:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva unidad"
        ctx["accion"] = "Crear"
        return ctx


class UnidadUpdateView(AdminRequiredMixin, UpdateView):
    model = Unidad
    template_name = "logistica/unidades/form.html"
    fields = ["numero_economico", "vin", "linea", "tipo", "sucursal_actual", "activo"]
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
def todos_los_registros(request):
    if not request.user.is_superuser and request.user.rol not in ("ADMIN", "CONTROL"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    movimientos = (
        Movimiento.objects
        .select_related("usuario", "sucursal")
        .prefetch_related("unidad_movimientos__unidad", "inspeccion")
        .order_by("-fecha_hora_evento")
    )
    return render(request, "logistica/movimientos/mis_registros.html", {
        "movimientos": movimientos,
        "mostrar_usuario": True,
        "active_nav": "todos_los_registros",
    })


@login_required
def mis_registros(request):
    if not request.user.is_superuser and request.user.rol != "CASETA":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    movimientos = (
        Movimiento.objects
        .filter(usuario=request.user)
        .select_related("sucursal")
        .prefetch_related("unidad_movimientos__unidad", "inspeccion")
        .order_by("-fecha_hora_evento")
    )
    return render(request, "logistica/movimientos/mis_registros.html", {
        "movimientos": movimientos,
    })


@login_required
def registrar_movimiento(request):
    if not request.user.is_superuser and request.user.rol != "CASETA":
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
    if not request.user.is_superuser and request.user.rol not in ("CASETA", "ADMIN"):
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
    if not request.user.is_superuser and request.user.rol not in ("CASETA", "ADMIN"):
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
    pass  # El estado se cierra explícitamente desde cerrar_inspeccion


@login_required
def sub_inspeccion_form(request, pk, sub_pk):
    if not request.user.is_superuser and request.user.rol not in ("CASETA", "ADMIN"):
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
    if not request.user.is_superuser and request.user.rol != "PLANEACION":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    manifiestos = (
        Manifiesto.objects
        .exclude(estado="CANCELADO")
        .select_related("sucursal_origen", "sucursal_destino", "usuario")
        .prefetch_related("unidad_manifiestos__unidad")
        .annotate(total_movimientos=Count("movimientos"))
        .order_by("-created_at")
    )
    return render(request, "logistica/manifiestos/list.html", {"manifiestos": manifiestos})


@login_required
def manifiesto_movimientos(request, pk):
    if not request.user.is_superuser and request.user.rol not in ("PLANEACION", "ADMIN", "CONTROL"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    manifiesto = get_object_or_404(
        Manifiesto.objects
        .select_related("sucursal_origen", "sucursal_destino", "usuario")
        .prefetch_related("unidad_manifiestos__unidad"),
        pk=pk,
    )
    movimientos = (
        manifiesto.movimientos
        .select_related("usuario", "sucursal")
        .prefetch_related("unidad_movimientos__unidad", "inspeccion")
        .order_by("fecha_hora_evento")
    )
    return render(request, "logistica/manifiestos/movimientos.html", {
        "manifiesto": manifiesto,
        "movimientos": movimientos,
    })


@login_required
@require_POST
def cerrar_inspeccion(request, pk):
    from django.core.exceptions import PermissionDenied
    if not request.user.is_superuser and request.user.rol not in ("CASETA", "ADMIN"):
        raise PermissionDenied

    inspeccion = get_object_or_404(Inspeccion, pk=pk)

    if inspeccion.estado != "EN_PROCESO":
        return redirect("inspeccion_detalle", pk=pk)

    subs = list(inspeccion.sub_inspecciones.all())
    if not subs or not all(s.completada for s in subs):
        return redirect("inspeccion_detalle", pk=pk)

    inspeccion.estado = "COMPLETADA"
    inspeccion.save(update_fields=["estado"])
    return redirect("inspeccion_detalle", pk=pk)


@login_required
def registrar_manifiesto(request):
    if not request.user.is_superuser and request.user.rol != "PLANEACION":
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
                numero_fianza=data.get("numero_fianza", ""),
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
    if not request.user.is_superuser and request.user.rol != "PLANEACION":
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
            manifiesto.numero_fianza      = data.get("numero_fianza", "")
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
            "numero_fianza":      manifiesto.numero_fianza,
            "observaciones":      manifiesto.observaciones,
        })

    return render(request, "logistica/manifiestos/form.html", {
        "form": form,
        "manifiesto": manifiesto,
        "active_nav": "manifiestos",
    })


@login_required
def inspeccion_pdf(request, pk):
    from django.core.exceptions import PermissionDenied
    if not request.user.is_superuser and request.user.rol not in ("CASETA", "ADMIN", "CONTROL"):
        raise PermissionDenied

    inspeccion = get_object_or_404(
        Inspeccion.objects.select_related(
            "movimiento__sucursal",
            "movimiento__usuario",
            "movimiento__manifiesto",
        ).prefetch_related(
            "movimiento__unidad_movimientos__unidad",
            "sub_inspecciones__detalle_general__marca_remolque",
            "sub_inspecciones__detalle_general__marca_contenedor",
            "sub_inspecciones__detalle_caja",
            "sub_inspecciones__detalle_caja_vacia",
            "sub_inspecciones__detalle_cinco_puntos",
            "sub_inspecciones__detalle_diecinueve_puntos",
            "sub_inspecciones__detalle_canina",
            "sub_inspecciones__detalle_medidas_remolque",
            "sub_inspecciones__llantas__posicion",
            "sub_inspecciones__llantas__marca",
            "sub_inspecciones__llantas__medida",
        ),
        pk=pk,
    )

    html_string = render_to_string(
        "logistica/inspecciones/pdf_reporte.html",
        {"inspeccion": inspeccion},
        request=request,
    )

    from weasyprint import HTML
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="inspeccion-{inspeccion.pk}.pdf"'
    return response


# ─── Dashboard de inspecciones ────────────────────────────────────────────────

_SINO_DETAIL_ATTR = {
    "CAJA":             "detalle_caja",
    "CAJA_VACIA":       "detalle_caja_vacia",
    "CINCO_PUNTOS":     "detalle_cinco_puntos",
    "DIECINUEVE_PUNTOS":"detalle_diecinueve_puntos",
    "CANINA":           "detalle_canina",
}


def _contar_negativos(sub):
    attr = _SINO_DETAIL_ATTR.get(sub.tipo)
    if not attr:
        return 0
    detalle = getattr(sub, attr, None)
    if detalle is None:
        return 0
    return sum(
        1 for f in detalle._meta.fields
        if getattr(f, "max_length", None) == 2 and getattr(detalle, f.name, "") == "NO"
    )


def _detalle_sino(sub):
    """Detalle con respuestas SI/NO de la sub-inspección, o None si no aplica/existe."""
    attr = _SINO_DETAIL_ATTR.get(sub.tipo)
    if not attr:
        return None
    try:
        return getattr(sub, attr)
    except ObjectDoesNotExist:
        return None


def _respuestas_sino(detalle):
    """{campo: valor} de los campos SI/NO de un detalle."""
    return {
        f.name: (getattr(detalle, f.name, "") or "")
        for f in detalle._meta.fields
        if getattr(f, "max_length", None) == 2
    }


@login_required
def dashboard_inspecciones(request):
    if not request.user.is_superuser and request.user.rol not in ("ADMIN", "CONTROL"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    sucursales = Sucursal.objects.filter(activo=True).order_by("nombre")
    return render(request, "logistica/supervisión/dashboard_inspecciones.html", {
        "sucursales": sucursales,
        "tipos_sub": TIPO_SUB_INSPECCION,
        "active_nav": "dashboard_inspecciones",
    })


@login_required
def api_dashboard_inspecciones(request):
    if not request.user.is_superuser and request.user.rol not in ("ADMIN", "CONTROL"):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    qs = (
        Inspeccion.objects
        .select_related(
            "movimiento__sucursal",
            "movimiento__manifiesto",
            "movimiento__usuario",
        )
        .prefetch_related(
            "movimiento__unidad_movimientos__unidad",
            "sub_inspecciones__detalle_caja",
            "sub_inspecciones__detalle_caja_vacia",
            "sub_inspecciones__detalle_cinco_puntos",
            "sub_inspecciones__detalle_diecinueve_puntos",
            "sub_inspecciones__detalle_canina",
        )
        .order_by("-movimiento__fecha_hora_evento")
    )

    # Filtros
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    sucursal_id = request.GET.get("sucursal_id")
    manifiesto_id = request.GET.get("manifiesto_id")
    tipo_sub = request.GET.get("tipo_sub")
    solo_alertas = request.GET.get("solo_alertas") == "1"

    if fecha_desde:
        qs = qs.filter(movimiento__fecha_hora_evento__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(movimiento__fecha_hora_evento__date__lte=fecha_hasta)
    if sucursal_id:
        qs = qs.filter(movimiento__sucursal_id=sucursal_id)
    if manifiesto_id:
        qs = qs.filter(movimiento__manifiesto_id=manifiesto_id)
    if tipo_sub:
        qs = qs.filter(sub_inspecciones__tipo=tipo_sub).distinct()

    inspecciones_data = []
    alertas_total = 0

    for insp in qs[:200]:
        mov = insp.movimiento
        tractores = []
        remolques = []
        for um in mov.unidad_movimientos.all():
            if um.unidad.tipo == "TRACTOR":
                tractores.append(um.unidad.numero_economico)
            else:
                remolques.append(um.unidad.numero_economico)

        subs_data = []
        total_neg = 0
        for sub in insp.sub_inspecciones.all():
            neg = _contar_negativos(sub)
            total_neg += neg
            subs_data.append({
                "id": sub.pk,
                "tipo": sub.tipo,
                "tipo_label": sub.get_tipo_display(),
                "completada": sub.completada,
                "negativos": neg,
            })

        tiene_alertas = total_neg > 0 or insp.estado == "RECHAZADA"
        if solo_alertas and not tiene_alertas:
            continue
        if tiene_alertas:
            alertas_total += 1

        manifiesto = mov.manifiesto
        inspecciones_data.append({
            "id": insp.pk,
            "estado": insp.estado,
            "estado_label": insp.get_estado_display(),
            "created_at": insp.created_at.strftime("%d/%m/%Y %H:%M"),
            "movimiento": {
                "id": mov.pk,
                "fecha": mov.fecha_hora_evento.strftime("%d/%m/%Y %H:%M"),
                "sucursal": mov.sucursal.nombre,
                "sucursal_id": mov.sucursal_id,
                "manifiesto": {
                    "id": manifiesto.pk,
                    "folio": manifiesto.folio_hoja_viajera or f"#{manifiesto.pk}",
                } if manifiesto else None,
                "tractores": tractores,
                "remolques": remolques,
            },
            "sub_inspecciones": subs_data,
            "tiene_alertas": tiene_alertas,
            "total_negativos": total_neg,
        })

    total = len(inspecciones_data)
    completadas = sum(1 for i in inspecciones_data if i["estado"] == "COMPLETADA")
    en_proceso  = sum(1 for i in inspecciones_data if i["estado"] == "EN_PROCESO")
    rechazadas  = sum(1 for i in inspecciones_data if i["estado"] == "RECHAZADA")

    manifiestos_qs = (
        Manifiesto.objects
        .filter(movimientos__isnull=False, movimientos__tipo="INSPECCION")
        .distinct()
        .order_by("-created_at")
        .values("id", "folio_hoja_viajera")[:100]
    )

    return JsonResponse({
        "inspecciones": inspecciones_data,
        "resumen": {
            "total": total,
            "completadas": completadas,
            "en_proceso": en_proceso,
            "rechazadas": rechazadas,
            "con_alertas": alertas_total,
        },
        "manifiestos": [
            {"id": m["id"], "folio": m["folio_hoja_viajera"] or f"#{m['id']}"}
            for m in manifiestos_qs
        ],
    })


@login_required
def api_manifiesto_timeline(request, pk):
    """Línea del tiempo de los movimientos de un manifiesto."""
    if not request.user.is_superuser and request.user.rol not in ("ADMIN", "CONTROL"):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    manifiesto = get_object_or_404(
        Manifiesto.objects.select_related("sucursal_origen", "sucursal_destino"),
        pk=pk,
    )

    movimientos = (
        manifiesto.movimientos
        .select_related("sucursal", "usuario", "inspeccion")
        .order_by("fecha_hora_evento")
    )

    eventos = []
    for mov in movimientos:
        try:
            insp = mov.inspeccion
        except Inspeccion.DoesNotExist:
            insp = None

        terminado = not mov.cancelado
        if insp is not None and insp.estado != "COMPLETADA":
            terminado = False

        eventos.append({
            "id": mov.pk,
            "tipo": mov.tipo,
            "tipo_label": mov.get_tipo_display(),
            "fecha": mov.fecha_hora_evento.strftime("%d/%m/%Y %H:%M"),
            "fecha_corta": mov.fecha_hora_evento.strftime("%d/%m/%Y"),
            "terminado": terminado,
            "sucursal": mov.sucursal.nombre,
            "sucursal_codigo": mov.sucursal.codigo,
            "estatus_caja": mov.get_estatus_caja_display() if mov.estatus_caja else "",
            "cancelado": mov.cancelado,
            "inconsistente": mov.inconsistente,
            "usuario": mov.usuario.get_full_name() or mov.usuario.username,
        })

    return JsonResponse({
        "manifiesto": {
            "id": manifiesto.pk,
            "folio": manifiesto.folio_hoja_viajera or f"#{manifiesto.pk}",
            "estado": manifiesto.get_estado_display(),
            "origen": manifiesto.sucursal_origen.nombre,
            "destino": manifiesto.sucursal_destino.nombre,
        },
        "eventos": eventos,
    })


@login_required
def api_dashboard_alertas(request):
    """Alertas operativas: hallazgos, inspecciones incompletas y movimientos inconsistentes."""
    if not request.user.is_superuser and request.user.rol not in ("ADMIN", "CONTROL"):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    sucursal_id = request.GET.get("sucursal_id")
    manifiesto_id = request.GET.get("manifiesto_id")
    tipo_sub = request.GET.get("tipo_sub")

    def _folio(manifiesto):
        if not manifiesto:
            return None
        return manifiesto.folio_hoja_viajera or f"#{manifiesto.pk}"

    alertas = []

    # ── Alertas de inspección (hallazgos / incompleta) ──
    insp_qs = (
        Inspeccion.objects
        .select_related("movimiento__sucursal", "movimiento__manifiesto")
        .prefetch_related(
            "sub_inspecciones__detalle_caja",
            "sub_inspecciones__detalle_caja_vacia",
            "sub_inspecciones__detalle_cinco_puntos",
            "sub_inspecciones__detalle_diecinueve_puntos",
            "sub_inspecciones__detalle_canina",
        )
        .order_by("-movimiento__fecha_hora_evento")
    )
    if fecha_desde:
        insp_qs = insp_qs.filter(movimiento__fecha_hora_evento__date__gte=fecha_desde)
    if fecha_hasta:
        insp_qs = insp_qs.filter(movimiento__fecha_hora_evento__date__lte=fecha_hasta)
    if sucursal_id:
        insp_qs = insp_qs.filter(movimiento__sucursal_id=sucursal_id)
    if manifiesto_id:
        insp_qs = insp_qs.filter(movimiento__manifiesto_id=manifiesto_id)
    if tipo_sub:
        insp_qs = insp_qs.filter(sub_inspecciones__tipo=tipo_sub).distinct()

    for insp in insp_qs[:300]:
        mov = insp.movimiento
        subs = list(insp.sub_inspecciones.all())
        total_neg = sum(_contar_negativos(s) for s in subs)
        base = {
            "fecha": mov.fecha_hora_evento.strftime("%d/%m/%Y %H:%M"),
            "fecha_iso": mov.fecha_hora_evento.isoformat(),
            "manifiesto": _folio(mov.manifiesto),
            "sucursal": mov.sucursal.nombre,
        }
        if total_neg > 0:
            alertas.append({
                **base,
                "tipo": "hallazgos",
                "tipo_label": "Con hallazgos",
                "severidad": "alta",
                "descripcion": f"{total_neg} hallazgo(s) en la inspección",
            })

    # ── Movimientos inconsistentes (no aplica si se filtra por tipo de sub-inspección) ──
    if not tipo_sub:
        mov_qs = (
            Movimiento.objects
            .filter(inconsistente=True)
            .select_related("sucursal", "manifiesto")
            .order_by("-fecha_hora_evento")
        )
        if fecha_desde:
            mov_qs = mov_qs.filter(fecha_hora_evento__date__gte=fecha_desde)
        if fecha_hasta:
            mov_qs = mov_qs.filter(fecha_hora_evento__date__lte=fecha_hasta)
        if sucursal_id:
            mov_qs = mov_qs.filter(sucursal_id=sucursal_id)
        if manifiesto_id:
            mov_qs = mov_qs.filter(manifiesto_id=manifiesto_id)

        for mov in mov_qs[:300]:
            alertas.append({
                "fecha": mov.fecha_hora_evento.strftime("%d/%m/%Y %H:%M"),
                "fecha_iso": mov.fecha_hora_evento.isoformat(),
                "manifiesto": _folio(mov.manifiesto),
                "sucursal": mov.sucursal.nombre,
                "tipo": "inconsistente",
                "tipo_label": "Movimiento inconsistente",
                "severidad": "alta",
                "descripcion": f"Movimiento «{mov.get_tipo_display()}» marcado como inconsistente",
            })

    # ── Cambio en respuestas entre inspecciones del mismo manifiesto ──
    comp_qs = (
        Inspeccion.objects
        .filter(movimiento__manifiesto__isnull=False)
        .select_related("movimiento__sucursal", "movimiento__manifiesto")
        .prefetch_related(
            "sub_inspecciones__detalle_caja",
            "sub_inspecciones__detalle_caja_vacia",
            "sub_inspecciones__detalle_cinco_puntos",
            "sub_inspecciones__detalle_diecinueve_puntos",
            "sub_inspecciones__detalle_canina",
        )
        .order_by("movimiento__manifiesto_id", "movimiento__fecha_hora_evento")
    )
    if manifiesto_id:
        comp_qs = comp_qs.filter(movimiento__manifiesto_id=manifiesto_id)

    _sino_lbl = {"SI": "Sí", "NO": "No"}
    ultimo = {}  # (manifiesto_id, tipo) -> {campo: última respuesta no vacía}

    for insp in comp_qs[:1000]:
        mov = insp.movimiento
        for sub in insp.sub_inspecciones.all():
            detalle = _detalle_sino(sub)
            if detalle is None:
                continue
            resp = _respuestas_sino(detalle)
            ref = ultimo.setdefault((mov.manifiesto_id, sub.tipo), {})

            cambios = []
            for campo, val in resp.items():
                if not val:
                    continue
                prev = ref.get(campo)
                if prev and prev != val:
                    cambios.append((campo, prev, val))
                ref[campo] = val

            if not cambios:
                continue
            if tipo_sub and sub.tipo != tipo_sub:
                continue
            if sucursal_id and str(mov.sucursal_id) != str(sucursal_id):
                continue
            fecha_dia = mov.fecha_hora_evento.date().isoformat()
            if fecha_desde and fecha_dia < fecha_desde:
                continue
            if fecha_hasta and fecha_dia > fecha_hasta:
                continue

            partes = [
                f"{detalle._meta.get_field(c).verbose_name}: "
                f"{_sino_lbl.get(p, p)}→{_sino_lbl.get(v, v)}"
                for c, p, v in cambios[:3]
            ]
            extra = f" (+{len(cambios) - 3})" if len(cambios) > 3 else ""
            alertas.append({
                "fecha": mov.fecha_hora_evento.strftime("%d/%m/%Y %H:%M"),
                "fecha_iso": mov.fecha_hora_evento.isoformat(),
                "manifiesto": _folio(mov.manifiesto),
                "sucursal": mov.sucursal.nombre,
                "tipo": "cambio_respuestas",
                "tipo_label": "Cambio en respuestas",
                "severidad": "alta",
                "descripcion": f"{sub.get_tipo_display()} — {'; '.join(partes)}{extra}",
            })

    # Pendiente: alerta por llantas cambiadas. Requiere capturar los cambios de
    # llanta autorizados en taller para poder contrastar lo inspeccionado
    # (RegistroLlanta) contra lo registrado para la unidad.

    alertas.sort(key=lambda a: a["fecha_iso"], reverse=True)

    return JsonResponse({"alertas": alertas})
