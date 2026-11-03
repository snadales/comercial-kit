"""Configuración de Django Admin para comercial-kit con simple-history (K1, K6, K7)."""

from django.contrib import admin, messages
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin
from comercial_kit.models import Parametro, ConsumidorToken, Aviso


@admin.register(Parametro)
class ParametroAdmin(SimpleHistoryAdmin):
    list_display = ("clave", "tipo", "valor_resumido", "descripcion")
    list_filter = ("tipo",)
    search_fields = ("clave", "descripcion", "valor")
    ordering = ("clave",)

    def valor_resumido(self, obj):
        val = obj.valor
        if len(val) > 60:
            return f"{val[:57]}..."
        return val
    valor_resumido.short_description = "Valor"


@admin.register(ConsumidorToken)
class ConsumidorTokenAdmin(SimpleHistoryAdmin):
    list_display = ("nombre", "alcance", "activo", "hash_resumido", "creado_en")
    list_filter = ("alcance", "activo")
    search_fields = ("nombre", "hash_token")
    readonly_fields = ("hash_token", "creado_en")
    actions = ["desactivar_tokens", "activar_tokens"]

    def hash_resumido(self, obj):
        return f"{obj.hash_token[:12]}..."
    hash_resumido.short_description = "Hash SHA-256"

    def save_model(self, request, obj, form, change):
        if not change and not obj.hash_token:
            # Creación inicial desde admin: generar token aleatorio
            _, raw_token = ConsumidorToken.crear_token(obj.nombre, obj.alcance)
            messages.success(
                request,
                format_html(
                    "<strong>Token creado exitosamente:</strong> <code>{}</code><br>"
                    "Guárdalo ahora; por seguridad no se podrá volver a mostrar.",
                    raw_token,
                ),
            )
            # obj ya fue creado en crear_token, evitamos super().save_model para no duplicar
            return
        super().save_model(request, obj, form, change)

    @admin.action(description="Desactivar tokens seleccionados")
    def desactivar_tokens(self, request, queryset):
        queryset.update(activo=False)

    @admin.action(description="Activar tokens seleccionados")
    def activar_tokens(self, request, queryset):
        queryset.update(activo=True)


@admin.register(Aviso)
class AvisoAdmin(SimpleHistoryAdmin):
    list_display = ("codigo", "nivel_badge", "objeto", "origen", "estado", "mensaje_corto", "creado_en")
    list_filter = ("nivel", "estado", "origen")
    search_fields = ("codigo", "objeto", "mensaje")
    readonly_fields = ("creado_en", "actualizado_en")
    actions = ["marcar_como_visto", "marcar_como_cerrado"]

    def nivel_badge(self, obj):
        colores = {
            Aviso.NIVEL_INFO: "#8A9AA8",
            Aviso.NIVEL_AVISO: "#E65C00",
            Aviso.NIVEL_CRITICO: "#FF3333",
        }
        color = colores.get(obj.nivel, "#8A9AA8")
        return format_html(
            '<span style="background-color: {}; color: #FFFFFF; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.nivel.upper(),
        )
    nivel_badge.short_description = "Nivel"

    def mensaje_corto(self, obj):
        return obj.mensaje[:70] + "..." if len(obj.mensaje) > 70 else obj.mensaje
    mensaje_corto.short_description = "Mensaje"

    @admin.action(description="Marcar como visto")
    def marcar_como_visto(self, request, queryset):
        queryset.update(estado=Aviso.ESTADO_VISTO)

    @admin.action(description="Marcar como cerrado")
    def marcar_como_cerrado(self, request, queryset):
        queryset.update(estado=Aviso.ESTADO_CERRADO)
