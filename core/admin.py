from django.contrib import admin

from .models import Pais, Partida, Perfil, ProgressoPais


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "capital", "continente")
    list_filter = ("continente",)
    search_fields = ("nome", "capital", "codigo")


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "pontos", "sequencia_dias", "acertos", "erros")
    search_fields = ("usuario__username",)


@admin.register(ProgressoPais)
class ProgressoPaisAdmin(admin.ModelAdmin):
    list_display = ("usuario", "pais", "acertos", "erros")
    list_filter = ("pais__continente",)


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "criada_em", "acertos", "total", "pontos", "finalizada")
