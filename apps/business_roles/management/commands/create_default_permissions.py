# apps/business_roles/management/commands/create_default_permissions.py

from django.core.management.base import BaseCommand
from apps.business_roles.models import BusinessPermission, BusinessRole
from apps.business.models import Business

# ✅ TODOS LOS PERMISOS DEL SISTEMA
PERMISSIONS_SEED = [
    # ── DASHBOARD ──────────────────────────────────────
    {'code': 'dashboard.view', 'name': 'Ver Dashboard', 'module': 'DASHBOARD'},
    
    # ── VENTAS ────────────────────────────────────────
    {'code': 'sales.view', 'name': 'Ver Ventas', 'module': 'SALES'},
    {'code': 'sales.create', 'name': 'Crear Ventas', 'module': 'SALES'},
    {'code': 'sales.edit', 'name': 'Editar Ventas', 'module': 'SALES'},
    {'code': 'sales.delete', 'name': 'Eliminar Ventas', 'module': 'SALES'},
    {'code': 'sales.approve', 'name': 'Aprobar Ventas', 'module': 'SALES'},
    {'code': 'sales.cancel', 'name': 'Cancelar Ventas', 'module': 'SALES'},
    {'code': 'sales.refund', 'name': 'Devoluciones', 'module': 'SALES'},
    
    # ── CLIENTES ──────────────────────────────────────
    {'code': 'customers.view', 'name': 'Ver Clientes', 'module': 'CUSTOMERS'},
    {'code': 'customers.create', 'name': 'Crear Clientes', 'module': 'CUSTOMERS'},
    {'code': 'customers.edit', 'name': 'Editar Clientes', 'module': 'CUSTOMERS'},
    {'code': 'customers.delete', 'name': 'Eliminar Clientes', 'module': 'CUSTOMERS'},
    
    # ── PRODUCTOS ─────────────────────────────────────
    {'code': 'products.view', 'name': 'Ver Productos', 'module': 'PRODUCTS'},
    {'code': 'products.create', 'name': 'Crear Productos', 'module': 'PRODUCTS'},
    {'code': 'products.edit', 'name': 'Editar Productos', 'module': 'PRODUCTS'},
    {'code': 'products.delete', 'name': 'Eliminar Productos', 'module': 'PRODUCTS'},
    
    # ── INVENTARIO ────────────────────────────────────
    {'code': 'inventory.read', 'name': 'Ver Inventario', 'module': 'INVENTORY'},
    {'code': 'inventory.adjust', 'name': 'Ajustar Stock', 'module': 'INVENTORY'},
    {'code': 'inventory.entry', 'name': 'Registrar Entradas', 'module': 'INVENTORY'},
    {'code': 'inventory.transfer', 'name': 'Transferir Stock', 'module': 'INVENTORY'},
    {'code': 'inventory.suppliers', 'name': 'Gestión Proveedores', 'module': 'INVENTORY'},
    
    # ── CAJA ──────────────────────────────────────────
    {'code': 'cashier.manage', 'name': 'Gestionar Caja', 'module': 'CASHIER'},
    {'code': 'cashier.open', 'name': 'Apertura de Caja', 'module': 'CASHIER'},
    {'code': 'cashier.close', 'name': 'Cierre de Caja', 'module': 'CASHIER'},
    {'code': 'cashier.view_daily', 'name': 'Ver Ventas del Día', 'module': 'CASHIER'},
    {'code': 'cashier.payments', 'name': 'Registrar Pagos', 'module': 'CASHIER'},
    
    # ── SERVICIOS ─────────────────────────────────────
    {'code': 'services.view', 'name': 'Ver Servicios', 'module': 'SERVICES'},
    {'code': 'services.create', 'name': 'Crear Órdenes', 'module': 'SERVICES'},
    {'code': 'services.edit', 'name': 'Editar Órdenes', 'module': 'SERVICES'},
    {'code': 'services.manage', 'name': 'Gestionar Servicios', 'module': 'SERVICES'},
    {'code': 'services.technical', 'name': 'Soporte Técnico', 'module': 'SERVICES'},
    {'code': 'services.parts', 'name': 'Registro Repuestos', 'module': 'SERVICES'},
    
    # ── USUARIOS ──────────────────────────────────────
    {'code': 'users.view', 'name': 'Ver Usuarios', 'module': 'USERS'},
    {'code': 'users.create', 'name': 'Crear Usuarios', 'module': 'USERS'},
    {'code': 'users.edit', 'name': 'Editar Usuarios', 'module': 'USERS'},
    {'code': 'users.delete', 'name': 'Eliminar Usuarios', 'module': 'USERS'},
    {'code': 'users.assign_roles', 'name': 'Asignar Roles', 'module': 'USERS'},
    
    # ── ROLES ─────────────────────────────────────────
    {'code': 'roles.view', 'name': 'Ver Roles', 'module': 'ROLES'},
    {'code': 'roles.create', 'name': 'Crear Roles', 'module': 'ROLES'},
    {'code': 'roles.edit', 'name': 'Editar Roles', 'module': 'ROLES'},
    {'code': 'roles.assign_permissions', 'name': 'Asignar Permisos', 'module': 'ROLES'},
    
    # ── MIEMBROS ──────────────────────────────────────
    {'code': 'members.view', 'name': 'Ver Miembros', 'module': 'MEMBERS'},
    
    # ── REPORTES ──────────────────────────────────────
    {'code': 'reports.view', 'name': 'Ver Reportes', 'module': 'REPORTS'},
    {'code': 'reports.financial', 'name': 'Reportes Financieros', 'module': 'REPORTS'},
    {'code': 'reports.sales', 'name': 'Reportes de Ventas', 'module': 'REPORTS'},
    {'code': 'reports.inventory', 'name': 'Reportes de Inventario', 'module': 'REPORTS'},
    {'code': 'reports.sales_basic', 'name': 'Reportes Básicos Ventas', 'module': 'REPORTS'},
    
    # ── AUDITORÍA ─────────────────────────────────────
    {'code': 'audit.view', 'name': 'Ver Auditoría', 'module': 'AUDIT'},
    
    # ── CONFIGURACIÓN ─────────────────────────────────
    {'code': 'business.update', 'name': 'Configurar Negocio', 'module': 'SETTINGS'},
    {'code': 'business.settings', 'name': 'Configuración Avanzada', 'module': 'SETTINGS'},
]

# ✅ ROLES CON SUS PERMISOS
ROLE_PERMISSIONS = {
    # ── ADMINISTRADOR (ACCESO TOTAL) ──────────────────
    "ADMIN": {
        "name": "Administrador",
        "description": "Gestiona toda la operación del negocio. Aprueba compras, supervisa ventas, consulta reportes.",
        "permissions": [perm['code'] for perm in PERMISSIONS_SEED],  # ← TODOS los permisos
        "is_default": True
    },
    
    # ── CAJERO ────────────────────────────────────────
    "CAJERO": {
        "name": "Cajero",
        "description": "Registrar cobros, pagos, apertura y cierre de caja. Consultar ventas del día.",
        "permissions": [
            'dashboard.view',
            'sales.view', 'sales.create',
            'cashier.manage', 'cashier.open', 'cashier.close', 'cashier.view_daily', 'cashier.payments',
            'customers.view', 'customers.create',
            'products.view',
            'reports.sales_basic',
        ],
        "is_default": True
    },
    
    # ── CONTADOR ──────────────────────────────────────
    "CONTADOR": {
        "name": "Contador",
        "description": "Gestión financiera, estados financieros, flujo de caja, impuestos, reportes contables.",
        "permissions": [
            'dashboard.view',
            'reports.view', 'reports.financial', 'reports.sales',
            'sales.view',
            'cashier.view_daily',
            'audit.view',
            'customers.view',
            'services.view',
            'users.view',
        ],
        "is_default": True
    },
    
    # ── ENCARGADO DE INVENTARIO ───────────────────────
    "INVENTARIO": {
        "name": "Encargado de Inventario",
        "description": "Registrar entradas y salidas, ajustes de stock, transferencias, gestión de proveedores, recepción de compras.",
        "permissions": [
            'dashboard.view',
            'inventory.read', 'inventory.adjust', 'inventory.entry', 'inventory.transfer', 'inventory.suppliers',
            'products.view', 'products.create', 'products.edit',
            'services.view', 'services.create', 'services.edit',
            'reports.inventory',
        ],
        "is_default": True
    },
    
    # ── SOPORTE TÉCNICO ───────────────────────────────
    "SOPORTE": {
        "name": "Soporte Técnico",
        "description": "Recepción de equipos, diagnóstico, reparaciones, registro de repuestos, entrega de equipos.",
        "permissions": [
            'dashboard.view',
            'services.view', 'services.create', 'services.edit', 'services.manage', 'services.technical', 'services.parts',
            'customers.view',
            'products.view',
            'inventory.read',
            'sales.view',
        ],
        "is_default": True
    },
    
    # ── VENDEDOR ──────────────────────────────────────
    "VENDEDOR": {
        "name": "Vendedor",
        "description": "Registrar clientes, crear cotizaciones, registrar ventas, consultar stock disponible, seguimiento de pedidos.",
        "permissions": [
            'dashboard.view',
            'sales.view', 'sales.create',
            'customers.view', 'customers.create', 'customers.edit',
            'products.view',
            'inventory.read',
            'services.view', 'services.create',
        ],
        "is_default": True
    },
}


class Command(BaseCommand):
    help = 'Crea todos los permisos del sistema y los 6 roles por defecto para cada negocio'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n🌱 INICIANDO: Creación de permisos y roles...\n'))
        
        # Paso 1: Crear permisos
        self.stdout.write("📋 Creando permisos base...")
        permissions = {}
        for perm_data in PERMISSIONS_SEED:
            perm, created = BusinessPermission.objects.get_or_create(
                code=perm_data['code'],
                defaults={
                    'name': perm_data['name'],
                    'module': perm_data['module'],
                    'description': perm_data.get('description', '')
                }
            )
            permissions[perm_data['code']] = perm
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ {perm_data["code"]}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ {len(permissions)} permisos creados/actualizados\n'))
        
        # Paso 2: Asignar roles a todos los negocios
        self.stdout.write("🏢 Asignando roles a negocios existentes...")
        businesses = Business.objects.all()
        total_roles_created = 0
        
        for business in businesses:
            self.stdout.write(self.style.WARNING(f'\n  Negocio: {business.name}'))
            
            for role_code, role_data in ROLE_PERMISSIONS.items():
                role, created = BusinessRole.objects.get_or_create(
                    business=business,
                    name=role_data['name'],
                    defaults={
                        'description': role_data['description'],
                        'is_default': role_data['is_default']
                    }
                )
                
                if created:
                    # Asignar permisos al rol
                    perm_codes = role_data['permissions']
                    role_perms = [permissions[code] for code in perm_codes if code in permissions]
                    role.permissions.set(role_perms)
                    total_roles_created += 1
                    self.stdout.write(self.style.SUCCESS(f'    ✅ Rol creado: {role_data["name"]} ({len(role_perms)} permisos)'))
                else:
                    self.stdout.write(self.style.WARNING(f'    ℹ️  Rol ya existe: {role_data["name"]}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 COMPLETADO: {total_roles_created} roles creados en {businesses.count()} negocios'))
        self.stdout.write(self.style.SUCCESS('\n💡 Ahora asigna los roles a los usuarios con:\n'))
        self.stdout.write(self.style.SUCCESS('   python manage.py shell\n'))
        self.stdout.write(self.style.SUCCESS('   >>> from apps.business_roles.management.commands.assign_admin_role import assign_admin_role\n'))
        self.stdout.write(self.style.SUCCESS('   >>> assign_admin_role("admin@techzone.com", "TechZone Norte")\n'))