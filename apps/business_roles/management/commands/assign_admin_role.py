# apps/business_roles/management/commands/assign_admin_role.py

from django.core.management.base import BaseCommand
from apps.authentication.models import CustomUser
from apps.business.models import Business, Membership
from apps.business_roles.models import BusinessUser, BusinessRole, BusinessUserRoleAssignment
from django.db import transaction

class Command(BaseCommand):
    help = 'Asigna el rol de Administrador a un usuario en un negocio específico'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario')
        parser.add_argument('business_name', type=str, help='Nombre del negocio')

    @transaction.atomic
    def handle(self, *args, **options):
        email = options['email']
        business_name = options['business_name']
        
        # Buscar usuario
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario no encontrado: {email}'))
            return
        
        # Buscar negocio
        try:
            business = Business.objects.get(name__iexact=business_name)
        except Business.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Negocio no encontrado: {business_name}'))
            return
        
        # Crear/actualizar Membership (para compatibilidad con login)
        membership, created = Membership.objects.get_or_create(
            user=user,
            business=business,
            defaults={'role': 'ADMIN', 'is_active': True}
        )
        if not created:
            membership.role = 'ADMIN'
            membership.is_active = True
            membership.save()
        
        # Crear BusinessUser
        business_user, created = BusinessUser.objects.get_or_create(
            user=user,
            business=business,
            defaults={
                'is_active': True,
                'position': 'Administrador',
                'department': 'Administración'
            }
        )
        
        # Buscar rol Admin
        try:
            admin_role = BusinessRole.objects.get(
                business=business,
                name='Administrador'
            )
        except BusinessRole.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Rol "Administrador" no encontrado en este negocio'))
            self.stdout.write(self.style.WARNING('💡 Ejecuta primero: python manage.py create_default_permissions'))
            return
        
        # Asignar rol
        assignment, created = BusinessUserRoleAssignment.objects.get_or_create(
            business_user=business_user,
            role=admin_role,
            defaults={
                'assigned_by': user,
                'is_active': True,
                'notes': 'Asignado como Administrador del negocio'
            }
        )
        
        if not created:
            assignment.is_active = True
            assignment.save()
        
        self.stdout.write(self.style.SUCCESS('\n✅ ÉXITO: Rol asignado correctamente\n'))
        self.stdout.write(f'👤 Usuario: {user.email}\n')
        self.stdout.write(f'🏢 Negocio: {business.name}\n')
        self.stdout.write(f'🎭 Rol: {admin_role.name}\n')
        self.stdout.write(f'🔑 Permisos: {admin_role.permissions.count()}\n')
        self.stdout.write(self.style.SUCCESS('\n🎉 El usuario ahora tiene acceso TOTAL al negocio\n'))