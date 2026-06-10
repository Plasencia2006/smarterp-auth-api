from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver


@receiver(post_migrate)
def create_default_business_roles(sender, **kwargs):
    """
    Crear roles base automáticamente después de ejecutar migraciones.
    Se ejecuta para CADA negocio existente en la base de datos.
    """
    
    # Solo ejecutar si es la app correcta
    if sender.label != 'business_roles':
        return
    
    try:
        # ✅ IMPORTAR CORRECTAMENTE
        from .models import BusinessRole
        from apps.business.models import Business  # ← Business está aquí
        
        # Roles base que debe tener cada negocio
        default_roles = [
            {
                'name': 'Administrador',
                'description': 'Gestiona toda la operación del negocio. Aprueba compras, anula ventas, gestiona usuarios.',
                'is_default': True,
            },
            {
                'name': 'Cajero',
                'description': 'Realiza cobros, abre y cierra caja, procesa pagos.',
                'is_default': True,
            },
            {
                'name': 'Vendedor',
                'description': 'Genera ventas, crea cotizaciones, gestiona clientes.',
                'is_default': True,
            },
            {
                'name': 'Encargado de Inventario',
                'description': 'Gestiona productos, stock, compras y proveedores.',
                'is_default': True,
            },
            {
                'name': 'Contador',
                'description': 'Genera facturas, reportes financieros, conciliaciones.',
                'is_default': True,
            },
            {
                'name': 'Soporte Técnico',
                'description': 'Gestiona tickets de soporte, servicios y mantenimientos.',
                'is_default': True,
            },
        ]
        
        # Obtener todos los negocios
        businesses = Business.objects.all()
        
        created_count = 0
        for business in businesses:
            for role_data in default_roles:
                _, created = BusinessRole.objects.get_or_create(
                    name=role_data['name'],
                    business=business,
                    defaults={
                        'description': role_data['description'],
                        'is_default': role_data['is_default'],
                    }
                )
                if created:
                    created_count += 1
        
        if created_count > 0:
            print(f"\n✅ [Signals] Se crearon {created_count} roles base para {businesses.count()} negocio(s)")
        else:
            print(f"\nℹ️  [Signals] Los roles base ya existen para {businesses.count()} negocio(s)")
            
    except Exception as e:
        print(f"❌ [Signals] Error creando roles base: {e}")


@receiver(post_save, sender='business.Business')
def create_roles_for_new_business(sender, instance, created, **kwargs):
    """
    Crear roles base automáticamente cuando se crea un NUEVO negocio.
    """
    if not created:
        return
    
    try:
        # ✅ IMPORTAR CORRECTAMENTE
        from .models import BusinessRole
        
        default_roles = [
            {
                'name': 'Administrador',
                'description': 'Gestiona toda la operación del negocio. Aprueba compras, anula ventas, gestiona usuarios.',
                'is_default': True,
            },
            {
                'name': 'Cajero',
                'description': 'Realiza cobros, abre y cierra caja, procesa pagos.',
                'is_default': True,
            },
            {
                'name': 'Vendedor',
                'description': 'Genera ventas, crea cotizaciones, gestiona clientes.',
                'is_default': True,
            },
            {
                'name': 'Encargado de Inventario',
                'description': 'Gestiona productos, stock, compras y proveedores.',
                'is_default': True,
            },
            {
                'name': 'Contador',
                'description': 'Genera facturas, reportes financieros, conciliaciones.',
                'is_default': True,
            },
            {
                'name': 'Soporte Técnico',
                'description': 'Gestiona tickets de soporte, servicios y mantenimientos.',
                'is_default': True,
            },
        ]
        
        for role_data in default_roles:
            BusinessRole.objects.get_or_create(
                name=role_data['name'],
                business=instance,
                defaults={
                    'description': role_data['description'],
                    'is_default': role_data['is_default'],
                }
            )
        
        print(f"\n✅ [Signals] Roles base creados para nuevo negocio: {instance.name}")
        
    except Exception as e:
        print(f"❌ [Signals] Error creando roles para nuevo negocio: {e}")