from django.apps import AppConfig

class BusinessRolesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.business_roles'
    verbose_name = 'Roles y Permisos de Negocio'

    def ready(self):
        import apps.business_roles.signals  # ← Importar signals