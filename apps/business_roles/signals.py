from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

@receiver(post_migrate)
def create_default_business_roles(sender, **kwargs):
    """Crear roles base después de migraciones (para negocios existentes)."""
    if sender.label != 'business_roles':
        return

    try:
        from .models import BusinessRole
        from apps.business.models import Business

        default_roles = [
            {'name': 'Administrador', 'description': 'Gestiona toda la operación del negocio.', 'is_default': True},
            {'name': 'Cajero', 'description': 'Realiza cobros, abre y cierra caja.', 'is_default': True},
            {'name': 'Vendedor', 'description': 'Genera ventas y cotizaciones.', 'is_default': True},
            {'name': 'Encargado de Inventario', 'description': 'Gestiona productos y stock.', 'is_default': True},
            {'name': 'Contador', 'description': 'Genera facturas y reportes financieros.', 'is_default': True},
            {'name': 'Soporte Técnico', 'description': 'Gestiona tickets y servicios.', 'is_default': True},
        ]

        businesses = Business.objects.all()
        created_count = 0
        
        for business in businesses:
            for role_data in default_roles:
                _, created = BusinessRole.objects.get_or_create(
                    name=role_data['name'],
                    business=business,
                    defaults={'description': role_data['description'], 'is_default': True}
                )
                if created:
                    created_count += 1

        if created_count > 0:
            print(f"\n✅ [Signals] Se crearon {created_count} roles base para {businesses.count()} negocio(s)")
        else:
            print(f"\nℹ️  [Signals] Los roles base ya existen para {businesses.count()} negocio(s)")

    except Exception as e:
        print(f"❌ [Signals] Error: {e}")


# ✅ IMPORTANTE: Usar el sender correcto
@receiver(post_save, sender='apps.business.Business')  # ← Cambiado de 'business.Business'
def create_roles_for_new_business(sender, instance, created, **kwargs):
    """Crear roles base cuando se crea un NUEVO negocio."""
    if not created:
        return

    try:
        from .models import BusinessRole

        default_roles = [
            {'name': 'Administrador', 'description': 'Gestiona toda la operación del negocio.', 'is_default': True},
            {'name': 'Cajero', 'description': 'Realiza cobros, abre y cierra caja.', 'is_default': True},
            {'name': 'Vendedor', 'description': 'Genera ventas y cotizaciones.', 'is_default': True},
            {'name': 'Encargado de Inventario', 'description': 'Gestiona productos y stock.', 'is_default': True},
            {'name': 'Contador', 'description': 'Genera facturas y reportes financieros.', 'is_default': True},
            {'name': 'Soporte Técnico', 'description': 'Gestiona tickets y servicios.', 'is_default': True},
        ]

        for role_data in default_roles:
            BusinessRole.objects.get_or_create(
                name=role_data['name'],
                business=instance,
                defaults={'description': role_data['description'], 'is_default': True}
            )

        print(f"\n✅ [Signals] Roles base creados para nuevo negocio: {instance.name}")

    except Exception as e:
        print(f"❌ [Signals] Error creando roles: {e}")