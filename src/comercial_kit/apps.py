from django.apps import AppConfig


class ComercialKitConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "comercial_kit"
    verbose_name = "Comercial Kit Navarino"

    def ready(self):
        # Asegurar inicialización y chequeos si corresponde
        pass
