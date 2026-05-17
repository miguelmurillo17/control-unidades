import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("logistica", "0008_inspeccion_via_movimiento"),
    ]

    operations = [
        # Eliminar PuntoRevision (reemplazado por modelos concretos)
        migrations.DeleteModel(name="PuntoRevision"),

        # Actualizar SubInspeccion: renombrar observaciones → comentarios, agregar fechas
        migrations.RenameField(
            model_name="subinspeccion",
            old_name="observaciones",
            new_name="comentarios",
        ),
        migrations.AddField(
            model_name="subinspeccion",
            name="fecha_hora_inicio",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="subinspeccion",
            name="fecha_hora_fin",
            field=models.DateTimeField(null=True, blank=True),
        ),

        # ── Catálogos ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name="Marca",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre",            models.CharField(max_length=100, unique=True)),
                ("aplica_llanta",     models.BooleanField(default=False)),
                ("aplica_remolque",   models.BooleanField(default=False)),
                ("aplica_contenedor", models.BooleanField(default=False)),
                ("activo",            models.BooleanField(default=True)),
            ],
            options={"ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="PosicionLlanta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre",                 models.CharField(max_length=20, unique=True)),
                ("requerir_en_inspeccion", models.BooleanField(default=True)),
            ],
            options={"ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="MedidaLlanta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("medida", models.CharField(max_length=30, unique=True)),
            ],
            options={"ordering": ["medida"]},
        ),
        migrations.CreateModel(
            name="ConfiguracionInspeccion",
            fields=[
                ("id",        models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("max_fotos", models.PositiveSmallIntegerField(default=5, verbose_name="Máximo de fotografías por sub-inspección")),
            ],
            options={"verbose_name": "Configuración de inspecciones", "verbose_name_plural": "Configuración de inspecciones"},
        ),

        # ── Fotografías ───────────────────────────────────────────────────────
        migrations.CreateModel(
            name="FotoSubInspeccion",
            fields=[
                ("id",             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("imagen",         models.ImageField(upload_to="inspecciones/fotos/")),
                ("etiqueta",       models.CharField(max_length=100, blank=True)),
                ("created_at",     models.DateTimeField(auto_now_add=True)),
                ("sub_inspeccion", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="fotos",
                    to="logistica.subinspeccion",
                )),
            ],
        ),

        # ── Detalles por tipo ─────────────────────────────────────────────────
        migrations.CreateModel(
            name="DetalleGeneral",
            fields=[
                ("id",               models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("id_caja",          models.CharField(verbose_name="ID caja",    max_length=50,  blank=True)),
                ("linea",            models.CharField(verbose_name="Línea",       max_length=100, blank=True)),
                ("placas",           models.CharField(max_length=20,  blank=True)),
                ("estado",           models.CharField(max_length=100, blank=True)),
                ("chofer",           models.CharField(max_length=100, blank=True)),
                ("id_tractor",       models.CharField(verbose_name="ID tractor", max_length=50,  blank=True)),
                ("fianza",           models.CharField(max_length=100, blank=True)),
                ("año_remolque",     models.PositiveSmallIntegerField(verbose_name="Año remolque",   null=True, blank=True)),
                ("vin_remolque",     models.CharField(verbose_name="VIN remolque",  max_length=50, blank=True)),
                ("año_contenedor",   models.PositiveSmallIntegerField(verbose_name="Año contenedor", null=True, blank=True)),
                ("vin_contenedor",   models.CharField(verbose_name="VIN contenedor", max_length=50, blank=True)),
                ("numero_sello",     models.CharField(verbose_name="Número de sello", max_length=50, blank=True)),
                ("sub_inspeccion",   models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="detalle_general",  to="logistica.subinspeccion")),
                ("marca_remolque",   models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="logistica.marca")),
                ("marca_contenedor", models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="logistica.marca")),
            ],
        ),
        migrations.CreateModel(
            name="DetalleCaja",
            fields=[
                ("id",                models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("remaches_de_carga", models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("manitas",           models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("patines",           models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("soqueteras",        models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("manivelas",         models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("golpes_y_rallones", models.CharField(verbose_name="Golpes y rayones", max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("reflejantes",       models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("molduras",          models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("sub_inspeccion",    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="detalle_caja", to="logistica.subinspeccion")),
            ],
        ),
        migrations.CreateModel(
            name="DetalleCajaVacia",
            fields=[
                ("id",                        models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("techo_libre_filtraciones",  models.CharField(verbose_name="Techo libre de filtraciones", max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("libre_olores",              models.CharField(verbose_name="Libre de olores",             max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("pisos_integros",            models.CharField(verbose_name="Pisos íntegros",              max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("paredes_integros",          models.CharField(verbose_name="Paredes íntegras",            max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("techos_integros",           models.CharField(verbose_name="Techos íntegros",             max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("bisagras",                  models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("mecanismos_de_cierre",      models.CharField(verbose_name="Mecanismos de cierre",        max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("puertas_simetricas",        models.CharField(verbose_name="Puertas simétricas",          max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("parches_y_reparaciones",    models.CharField(verbose_name="Parches y reparaciones",      max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("limpieza",                  models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("paredes_de_interior",       models.CharField(verbose_name="Paredes de interior",         max_length=2, choices=[("SI","Sí"),("NO","No"),("NA","N/A")], blank=True)),
                ("sub_inspeccion",            models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="detalle_caja_vacia", to="logistica.subinspeccion")),
            ],
        ),
        migrations.CreateModel(
            name="RegistroLlanta",
            fields=[
                ("id",             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cautin",         models.CharField(verbose_name="Cautín", max_length=50, blank=True)),
                ("origen",         models.CharField(max_length=100, blank=True)),
                ("validado",       models.BooleanField(default=False)),
                ("sub_inspeccion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="llantas", to="logistica.subinspeccion")),
                ("posicion",       models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="logistica.posicionllanta")),
                ("marca",          models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="logistica.marca")),
                ("medida",         models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to="logistica.medidallanta")),
            ],
            options={"unique_together": {("sub_inspeccion", "posicion")}},
        ),
        migrations.CreateModel(
            name="DetalleCincoPuntos",
            fields=[
                ("id",                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ver_sellos",         models.CharField(verbose_name="Vea sellos y mecanismos",       max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("verificar_sello",    models.CharField(verbose_name="Verifique número de sello",     max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("tirar_sello",        models.CharField(verbose_name="Tire del sello",                max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("torcer_sello",       models.CharField(verbose_name="Tuerza y gire el sello",        max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("verificar_bisagra",  models.CharField(verbose_name="Verifique bisagras aseguradas", max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("sub_inspeccion",     models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="detalle_cinco_puntos", to="logistica.subinspeccion")),
            ],
        ),
        migrations.CreateModel(
            name="DetalleDiecinuevePuntos",
            fields=[
                ("id",                       models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("defensa",                  models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("llantas_y_rines",          models.CharField(verbose_name="Llantas y rines",          max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("piso_tractor",             models.CharField(verbose_name="Piso del tractor",         max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("tanque_gasolina",          models.CharField(verbose_name="Tanque de gasolina",       max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("interior_cabina",          models.CharField(verbose_name="Interior de cabina",       max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("tanques_de_aire",          models.CharField(verbose_name="Tanques de aire",          max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("chasis_y_quinta_rueda",    models.CharField(verbose_name="Chasis y quinta rueda",    max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("ejes_de_transmision",      models.CharField(verbose_name="Ejes de transmisión",      max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("tubo_de_escape",           models.CharField(verbose_name="Tubo de escape",           max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("motor",                    models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("base_del_remolque",        models.CharField(verbose_name="Base del remolque",        max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("puertas_interiores",       models.CharField(verbose_name="Puertas interiores",       max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("pared_lateral_derecha",    models.CharField(verbose_name="Pared lateral derecha",    max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("techo_interno_y_externo",  models.CharField(verbose_name="Techo interno y externo",  max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("pared_frontal",            models.CharField(verbose_name="Pared frontal",            max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("pared_lateral_izquierda",  models.CharField(verbose_name="Pared lateral izquierda",  max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("piso_interno",             models.CharField(verbose_name="Piso interno",             max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("eje_palanca_patin",        models.CharField(verbose_name="Eje palanca/patín",        max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("sistema_refrigeracion",    models.CharField(verbose_name="Sistema de refrigeración", max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("sub_inspeccion",           models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="detalle_diecinueve_puntos", to="logistica.subinspeccion")),
            ],
        ),
        migrations.CreateModel(
            name="DetalleCanina",
            fields=[
                ("id",             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("aprobado",       models.CharField(max_length=2, choices=[("SI","Sí"),("NO","No")], blank=True)),
                ("sub_inspeccion", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="detalle_canina", to="logistica.subinspeccion")),
            ],
        ),
        migrations.CreateModel(
            name="DetalleMedidasRemolque",
            fields=[
                ("id",             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("largo",          models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="metros")),
                ("ancho",          models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="metros")),
                ("alto",           models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="metros")),
                ("sub_inspeccion", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="detalle_medidas_remolque", to="logistica.subinspeccion")),
            ],
        ),
    ]
