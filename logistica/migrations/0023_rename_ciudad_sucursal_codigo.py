from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("logistica", "0022_remove_validado_from_registrollanta"),
    ]

    operations = [
        migrations.RenameField(
            model_name="sucursal",
            old_name="ciudad",
            new_name="codigo",
        ),
    ]
