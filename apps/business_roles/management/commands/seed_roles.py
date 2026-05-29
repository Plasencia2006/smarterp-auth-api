from django.core.management.base import BaseCommand
from apps.business_roles.models import BusinessPermission, BusinessRole
from apps.business.models import Business  # Ajusta si tu app de negocios tiene otro nombre

# Mapa exacto de los 5 roles y sus permisos
ROLE_PERMISSIONS = {
    "Vendedor": [
        "sales.create", "sales.view", "customers.view", "customers.create", 
        "products.view", "services.create", "services.view"
    ],
    "Encargado de Inventario": [
        "inventory.read", "inventory.adjust", "inventory.entry", 
        "products.view", "products.create", "products.update", "reports.inventory"
    ],
    "Cajero": [
        "sales.create", "sales.view", "cashier.manage", "products.view", 
        "customers.view", "reports.sales_basic"
    ],
    "Contador": [
        "reports.view", "reports.financial", "sales.view", "users.view", 
        "services.view", "customers.view"
    ],
    "Soporte Técnico": [
        "services.manage", "services.create", "services.update", 
        "customers.view", "products.view", "inventory.read"
    ]
}

PERMISSIONS_SEED = [
    {'code': 'sales.create', 'name': 'Crear ventas', 'module': 'SALES'},
    {'code': 'sales.view', 'name': 'Ver ventas', 'module': 'SALES'},
    {'code': 'sales.cancel', 'name': 'Cancelar ventas', 'module': 'SALES'},
    {'code': 'cashier.manage', 'name': 'Gestionar caja', 'module': 'SALES'},
    {'code': 'customers.view', 'name': 'Ver clientes', 'module': 'CUSTOMERS'},
    {'code': 'customers.create', 'name': 'Crear clientes', 'module': 'CUSTOMERS'},
    {'code': 'products.view', 'name': 'Ver productos', 'module': 'INVENTORY'},
    {'code': 'products.create', 'name': 'Crear productos', 'module': 'INVENTORY'},
    {'code': 'products.update', 'name': 'Editar productos', 'module': 'INVENTORY'},
    {'code': 'inventory.read', 'name': 'Ver inventario', 'module': 'INVENTORY'},
    {'code': 'inventory.adjust', 'name': 'Ajustar stock', 'module': 'INVENTORY'},
    {'code': 'inventory.entry', 'name': 'Registrar entradas', 'module': 'INVENTORY'},
    {'code': 'services.create', 'name': 'Crear órdenes', 'module': 'SERVICES'},
    {'code': 'services.view', 'name': 'Ver órdenes', 'module': 'SERVICES'},
    {'code': 'services.update', 'name': 'Actualizar estado', 'module': 'SERVICES'},
    {'code': 'services.manage', 'name': 'Gestionar servicios', 'module': 'SERVICES'},
    {'code': 'reports.view', 'name': 'Ver reportes', 'module': 'REPORTS'},
    {'code': 'reports.financial', 'name': 'Reportes financieros', 'module': 'REPORTS'},
    {'code': 'reports.sales_basic', 'name': 'Reportes básicos de ventas', 'module': 'REPORTS'},
    {'code': 'reports.inventory', 'name': 'Reportes de inventario', 'module': 'REPORTS'},
    {'code': 'users.view', 'name': 'Ver usuarios', 'module': 'USERS'},
    {'code': 'users.create', 'name': 'Crear usuarios', 'module': 'USERS'},
]

class Command(BaseCommand):
    help = 'Crea permisos base y asigna los 5 roles por defecto a todos los negocios'

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Creando permisos base...")
        for perm in PERMISSIONS_SEED:
            BusinessPermission.objects.get_or_create(code=perm['code'], defaults=perm)
            
        self.stdout.write("🏢 Asignando roles base a negocios...")
        businesses = Business.objects.all()
        for business in businesses:
            for role_name, perm_codes in ROLE_PERMISSIONS.items():
                role, created = BusinessRole.objects.get_or_create(
                    business=business,
                    name=role_name,
                    defaults={'description': f'Rol base: {role_name}', 'is_default': True}
                )
                if created:
                    perms = BusinessPermission.objects.filter(code__in=perm_codes)
                    role.permissions.set(perms)
                    
        self.stdout.write(self.style.SUCCESS('✅ Roles y permisos configurados correctamente.'))