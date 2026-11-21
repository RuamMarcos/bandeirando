from django.db import migrations

from core.dados_paises import PAISES


def carregar(apps, schema_editor):
    Pais = apps.get_model("core", "Pais")
    Pais.objects.bulk_create(
        [Pais(codigo=c, nome=n, capital=cap, continente=cont) for c, n, cap, cont in PAISES],
        ignore_conflicts=True,
    )


def descarregar(apps, schema_editor):
    apps.get_model("core", "Pais").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(carregar, descarregar)]
