from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from django.db.models import Count, Q

from .forms import MovimientoForm, ManifiestoForm, SubInspeccionForm, DetalleGeneralForm, DetalleCajaForm
from .models import DetalleGeneral, DetalleCaja, Inspeccion, Manifiesto, Movimiento, SubInspeccion, Sucursal, Unidad, UnidadManifiesto
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
            completadas_subs=Count("sub_inspecciones", filter=Q(sub_inspecciones__resultado__gt="")),
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
    completadas = sum(1 for s in sub_inspecciones if s.resultado)
    total       = len(sub_inspecciones)

    return render(request, "logistica/inspecciones/detalle.html", {
        "inspeccion":     inspeccion,
        "sub_inspecciones": sub_inspecciones,
        "completadas":    completadas,
        "total":          total,
        "porcentaje":     int(completadas / total * 100) if total else 0,
    })


def _marcar_completada_si_aplica(inspeccion):
    todas = inspeccion.sub_inspecciones.all()
    if all(s.resultado for s in todas):
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

    # Formulario genérico para tipos aún no implementados
    if request.method == "POST":
        form = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        if form.is_valid():
            sub = form.save(commit=False)
            if sub.resultado:
                from django.utils import timezone
                sub.fecha_hora_fin = timezone.now()
            sub.save()
            _marcar_completada_si_aplica(inspeccion)
            return redirect("inspeccion_detalle", pk=inspeccion.pk)
    else:
        form = SubInspeccionForm(instance=sub_inspeccion)

    return render(request, "logistica/inspecciones/sub_form.html", {
        "inspeccion":     inspeccion,
        "sub_inspeccion": sub_inspeccion,
        "form":           form,
    })


def _sub_form_general(request, inspeccion, sub_inspeccion):
    detalle = DetalleGeneral.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form    = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleGeneralForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            sub = sub_form.save(commit=False)
            if sub.resultado:
                from django.utils import timezone
                sub.fecha_hora_fin = timezone.now()
            sub.save()
            det = detalle_form.save(commit=False)
            det.sub_inspeccion = sub_inspeccion
            det.save()
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
    })


def _sub_form_caja(request, inspeccion, sub_inspeccion):
    detalle = DetalleCaja.objects.filter(sub_inspeccion=sub_inspeccion).first()

    if request.method == "POST":
        sub_form     = SubInspeccionForm(request.POST, instance=sub_inspeccion)
        detalle_form = DetalleCajaForm(request.POST, instance=detalle)
        if sub_form.is_valid() and detalle_form.is_valid():
            sub = sub_form.save(commit=False)
            if sub.resultado:
                from django.utils import timezone
                sub.fecha_hora_fin = timezone.now()
            sub.save()
            det = detalle_form.save(commit=False)
            det.sub_inspeccion = sub_inspeccion
            det.save()
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
