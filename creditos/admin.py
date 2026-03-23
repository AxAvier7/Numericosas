from django.contrib import admin
from .models import Perfil, Envio, ValorCP, ValorPredeterminado, Revision

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'creditos')
    list_filter = ('tipo', 'creditos')
    search_fields = ('usuario__username',)

@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'tipo', 'fecha_envio', 'aceptado', 'creditos_otorgados')
    list_filter = ('tipo', 'aceptado', 'fecha_envio')
    search_fields = ('estudiante__username',)
    readonly_fields = ('fecha_envio',)

@admin.register(ValorCP)
class ValorCPAdmin(admin.ModelAdmin):
    list_display = ('numero_cp', 'numero_inciso', 'valor_defecto')
    list_filter = ('numero_cp',)
    search_fields = ('numero_cp',)

@admin.register(ValorPredeterminado)
class ValorPredeterminadoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'valor_defecto')
    list_filter = ('tipo',)
    search_fields = ('tipo',)

@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    list_display = ('envio', 'profesor', 'aceptado', 'creditos_otorgados', 'fecha_revision')
    list_filter = ('aceptado', 'fecha_revision')
    search_fields = ('profesor__username',)
    readonly_fields = ('fecha_revision',)

