import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("logistica", "0006_manifiesto_folio_hoja_viajera"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Drop old inspection tables
        migrations.DeleteModel(name="DetalleInspeccion"),
        migrations.DeleteModel(name="Inspeccion"),

        # PlantillaPunto catalog
        migrations.CreateModel(
            name="PlantillaPunto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo_sub", models.CharField(
                    max_length=30,
                    choices=[
                        ("GENERAL",           "Inspección general"),
                        ("CAJA",              "Inspección de caja"),
                        ("CAJA_VACIA",        "Inspección de caja vacía"),
                        ("LLANTAS",           "Inspección de llantas"),
                        ("CINCO_PUNTOS",      "Inspección 5 puntos VVTTB"),
                        ("DIECINUEVE_PUNTOS", "Inspección 19 puntos de seguridad"),
                        ("CANINA",            "Inspección canina"),
                        ("MEDIDAS_REMOLQUE",  "Inspección de medidas de remolques vacíos"),
                    ],
                )),
                ("descripcion", models.CharField(max_length=200)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                ("activo", models.BooleanField(default=True)),
            ],
            options={"ordering": ["tipo_sub", "orden"]},
        ),

        # New Inspeccion
        migrations.CreateModel(
            name="Inspeccion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateTimeField(null=True, blank=True)),
                ("estado", models.CharField(
                    max_length=20,
                    choices=[("EN_PROCESO", "En proceso"), ("COMPLETADA", "Completada"), ("RECHAZADA", "Rechazada")],
                    default="EN_PROCESO",
                )),
                ("observaciones", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("manifiesto", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="inspecciones",
                    to="logistica.manifiesto",
                )),
                ("inspector", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="inspecciones",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),

        # SubInspeccion
        migrations.CreateModel(
            name="SubInspeccion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(
                    max_length=30,
                    choices=[
                        ("GENERAL",           "Inspección general"),
                        ("CAJA",              "Inspección de caja"),
                        ("CAJA_VACIA",        "Inspección de caja vacía"),
                        ("LLANTAS",           "Inspección de llantas"),
                        ("CINCO_PUNTOS",      "Inspección 5 puntos VVTTB"),
                        ("DIECINUEVE_PUNTOS", "Inspección 19 puntos de seguridad"),
                        ("CANINA",            "Inspección canina"),
                        ("MEDIDAS_REMOLQUE",  "Inspección de medidas de remolques vacíos"),
                    ],
                )),
                ("resultado", models.CharField(
                    max_length=20,
                    choices=[("APROBADO", "Aprobado"), ("RECHAZADO", "Rechazado"), ("NA", "No aplica")],
                    blank=True,
                )),
                ("observaciones", models.TextField(blank=True)),
                ("inspeccion", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="sub_inspecciones",
                    to="logistica.inspeccion",
                )),
            ],
            options={"unique_together": {("inspeccion", "tipo")}},
        ),

        # PuntoRevision
        migrations.CreateModel(
            name="PuntoRevision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("descripcion", models.CharField(max_length=200)),
                ("resultado", models.CharField(
                    max_length=5,
                    choices=[("SI", "Sí"), ("NO", "No"), ("NA", "N/A")],
                    blank=True,
                )),
                ("comentario", models.TextField(blank=True)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                ("plantilla_punto", models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    to="logistica.plantillapunto",
                )),
                ("sub_inspeccion", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="puntos",
                    to="logistica.subinspeccion",
                )),
            ],
            options={"ordering": ["orden"]},
        ),
    ]
