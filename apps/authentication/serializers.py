# apps/authentication/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


# =============================================================================
# ✅ 1. SERIALIZER PARA LOGIN (JWT) - CON MEMBRESÍAS, ROLES Y PERMISOS
# =============================================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['username'] = user.username
        token['is_super_admin'] = getattr(user, 'is_super_admin', False) or user.is_superuser
        return token

    def validate(self, attrs):
        # Validar credenciales básicas (email/password)
        data = super().validate(attrs)
        user = self.user
        
        # ✅ 1️⃣ VALIDAR: CustomUser.is_active (usuario global)
        if not user.is_active:
            raise serializers.ValidationError({
                'detail': 'Tu cuenta ha sido desactivada. Contacta al administrador.'
            })
        
        # ✅ 2️⃣ VALIDAR: estado del usuario
        estado = getattr(user, 'estado', 'ACTIVO').upper()
        if estado in ['SUSPENDIDO', 'INACTIVO', 'ELIMINADO']:
            raise serializers.ValidationError({
                'detail': f'Tu cuenta está {estado.lower()}. Contacta al administrador.'
            })
        
        # ✅ 3️⃣ VALIDAR: Super Admin NO necesita memberships
        is_super = getattr(user, 'is_super_admin', False) or user.is_superuser
        
        from apps.business.models import Membership
        from apps.business_roles.models import BusinessRole, BusinessPermission
        
        memberships_data = []
        all_roles = []
        all_permissions = []
        
        if is_super:
            # ✅ SUPER ADMIN: No necesita memberships, tiene acceso total
            print(f"✅ [Login] {user.email} - SUPER ADMIN detectado")
            
            # Darle todos los permisos del sistema
            all_perms = BusinessPermission.objects.all()
            unique_permissions = [
                {'code': p.code, 'name': p.name, 'module': p.module}
                for p in all_perms
            ]
            
        else:
            # ✅ USUARIO NORMAL: Validar memberships
            memberships = Membership.objects.filter(
                user=user, 
                is_active=True
            ).select_related('business')
            
            # Si NO tiene memberships activos, no puede iniciar sesión
            if not memberships.exists():
                # Verificar si tiene memberships pero están inactivos
                has_inactive_membership = Membership.objects.filter(
                    user=user, 
                    is_active=False
                ).exists()
                
                if has_inactive_membership:
                    raise serializers.ValidationError({
                        'detail': 'Tu acceso a este negocio ha sido desactivado. Contacta al administrador.'
                    })
                else:
                    raise serializers.ValidationError({
                        'detail': 'No tienes acceso a ningún negocio. Contacta al administrador.'
                    })
            
            # ✅ 4️⃣ VALIDAR: BusinessUser.is_active (si existe)
            from apps.business_roles.models import BusinessUser
            
            for membership in memberships:
                try:
                    business_user = BusinessUser.objects.get(
                        user=user, 
                        business=membership.business
                    )
                    if not business_user.is_active:
                        raise serializers.ValidationError({
                            'detail': f'Tu cuenta en {membership.business.name} está inactiva. Contacta al administrador.'
                        })
                except BusinessUser.DoesNotExist:
                    # Si es solo un admin de negocio (no BusinessUser), está bien
                    pass
            
            # Extraer memberships y roles
            for m in memberships:
                user_roles = BusinessRole.objects.filter(
                    business=m.business,
                    user_assignments__business_user__user=user,
                    user_assignments__is_active=True
                ).prefetch_related('permissions')
                
                roles_serialized = []
                
                for role in user_roles:
                    perms = [
                        {'code': p.code, 'name': p.name, 'module': p.module}
                        for p in role.permissions.all()
                    ]
                    roles_serialized.append({
                        'id': str(role.id),
                        'name': role.name,
                        'permissions': perms
                    })
                    all_permissions.extend(perms)
                
                if not user_roles and m.role and m.role.upper() == 'ADMIN':
                    all_perms = BusinessPermission.objects.all()
                    perms = [
                        {'code': p.code, 'name': p.name, 'module': p.module}
                        for p in all_perms
                    ]
                    roles_serialized.append({
                        'id': None,
                        'name': 'Administrador',
                        'permissions': perms
                    })
                    all_permissions.extend(perms)
                
                memberships_data.append({
                    'id': str(m.id),
                    'business': str(m.business.id) if m.business else None,
                    'business_name': m.business.name if m.business else 'Sin nombre',
                    'membership_role': m.role,
                    'is_active': m.is_active,
                    'roles': roles_serialized
                })
                
                all_roles.extend(roles_serialized)
            
            # Eliminar duplicados
            seen_codes = set()
            unique_permissions = []
            for perm in all_permissions:
                if perm['code'] not in seen_codes:
                    unique_permissions.append(perm)
                    seen_codes.add(perm['code'])
        
        # ✅ INCLUIR EN LA RESPUESTA
        data['user'] = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'is_super_admin': is_super,
            'estado': estado,
            'is_active': user.is_active,
            'business_memberships': memberships_data,
            'roles': all_roles,
            'permissions': unique_permissions if is_super else unique_permissions
        }
        
        print(f"✅ [Login] {user.email} - Login exitoso")
        print(f"✅ [Login] Is Super Admin: {is_super}")
        print(f"✅ [Login] Memberships: {len(memberships_data)}")
        print(f"✅ [Login] Permissions: {len(unique_permissions)}")
        
        return data


# =============================================================================
# ✅ 2. SERIALIZER PARA CREAR USUARIOS (REGISTRO)
# =============================================================================
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializador para crear nuevos usuarios.
    Hashea la contraseña automáticamente con create_user().
    """
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'is_super_admin', 'estado'
        )

    def validate(self, attrs):
        # Validar que las contraseñas coincidan
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        
        # ✅ IMPORTANTE: Eliminar password_confirm del validated_data
        attrs.pop('password_confirm', None)
        
        return attrs

    def create(self, validated_data):
        """
        Crear usuario con contraseña hasheada.
        ✅ USAR create_user() que hashea automáticamente
        """
        # Eliminar password_confirm si aún existe
        validated_data.pop('password_confirm', None)
        
        # Obtener la contraseña
        password = validated_data.pop('password', None)
        
        if not password:
            raise serializers.ValidationError({"password": "La contraseña es requerida."})
        
        # ✅ create_user() YA HASHEA la contraseña automáticamente
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=password,  # ← Se hashea automáticamente
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_super_admin=validated_data.get('is_super_admin', False),
            estado=validated_data.get('estado', 'ACTIVO'),
            is_active=True
        )
        
        print(f"✅ Usuario creado: {user.id} - {user.email}")
        print(f"✅ Password hasheada: {user.password[:50]}...")
        print(f"✅ Password is NULL: {user.password is None}")
        
        return user
    


# =============================================================================
# ✅ 3. SERIALIZER PARA LISTAR USUARIOS (SOLO LECTURA)
# =============================================================================
class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para ver la lista de usuarios o detalles.
    NO incluye campos de escritura como password.
    """
    is_super_admin = serializers.SerializerMethodField()
    # ✅ AGREGAR: Campo para las membresías del negocio
    business_memberships = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'estado', 'is_super_admin', 'date_joined', 'last_login',
            'business_memberships'  # ← Ya lo tenías, perfecto
        )
        read_only_fields = ('id', 'date_joined', 'last_login')

    def get_is_super_admin(self, obj):
        return getattr(obj, 'is_super_admin', False) or obj.is_superuser

    # ✅ AGREGAR ESTE MÉTODO: Obtener membresías del usuario
    def get_business_memberships(self, obj):
        """
        Obtener las membresías activas del usuario en los negocios.
        Esto es CLAVE para que el frontend pueda filtrar Admins de Negocio.
        """
        from apps.business.models import Membership
        
        # Obtener membresías activas del usuario
        memberships = Membership.objects.filter(
            user=obj,
            is_active=True
        ).select_related('business')  # Optimización: evitar N+1 queries
        
        # Serializar las membresías
        return [
            {
                'id': str(m.id),
                'business': str(m.business.id),  # ID del negocio
                'business_name': m.business.name,  # Nombre legible
                'role': m.role,  # Rol en la membresía (ADMIN, VENDEDOR, etc.)
                'membership_role': m.role,  # Alias para compatibilidad
                'is_active': m.is_active
            }
            for m in memberships
        ]

# =============================================================================
# ✅ 4. SERIALIZER PARA DETALLE DE PERFIL (/me/)
# =============================================================================
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # ← CAMBIA 'CustomUser' POR 'User'
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_active', 'is_super_admin',
            'last_login', 'date_joined'
        ]
        read_only_fields = ['id', 'last_login', 'date_joined']
    
    def update(self, instance, validated_data):
        if 'is_super_admin' in validated_data:
            instance.is_super_admin = validated_data['is_super_admin']
            instance.save(update_fields=['is_super_admin'])
        
        return super().update(instance, validated_data)

# =============================================================================
# ✅ 5. SERIALIZER PARA ACTUALIZAR USUARIOS (PERMITE EDICIÓN)
# =============================================================================
class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para actualizar usuarios existentes.
    Password es opcional - solo se actualiza si se proporciona.
    Username solo editable si el usuario nunca ha iniciado sesión.
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'is_active', 'is_super_admin', 'estado'
        ]
        extra_kwargs = {
            'username': {'required': False, 'allow_blank': True, 'max_length': 150},
            'email': {'required': False, 'allow_blank': True},
            'first_name': {'required': False, 'allow_blank': True, 'max_length': 150},
            'last_name': {'required': False, 'allow_blank': True, 'max_length': 150},
            'is_active': {'required': False},
            'is_super_admin': {'required': False},
            'estado': {'required': False},
        }
    
    def validate_username(self, value):
        """Validar username: solo editable antes del primer login"""
        if value == '' or value is None:
            return self.instance.username
        
        if value == self.instance.username:
            return value
        
        # Regla: solo permitir cambiar username si NUNCA ha iniciado sesión
        if self.instance.last_login is not None:
            raise serializers.ValidationError(
                "El nombre de usuario solo puede modificarse antes del primer inicio de sesión."
            )
        
        # Verificar unicidad
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        
        # Validar formato Django
        from django.core.validators import RegexValidator
        validator = RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='El username solo puede contener letras, números y @/./+/-/_'
        )
        try:
            validator(value)
        except:
            raise serializers.ValidationError(
                "El username solo puede contener letras, números y @/./+/-/_"
            )
        
        return value
    
    def validate_email(self, value):
        """Validar email"""
        if value == '' or value is None:
            return self.instance.email
        
        from django.core.validators import validate_email
        try:
            validate_email(value)
        except:
            raise serializers.ValidationError("Ingresa un email válido.")
        
        return value
    
    def validate_password(self, value):
        """Ignorar password si está vacío"""
        if value == '' or value is None:
            return None
        return value
    
    def update(self, instance, validated_data):
        """Actualizar usuario y contraseña (si se proporcionó)"""
        # Password especial
        password = validated_data.get('password')
        if password and password.strip():
            instance.set_password(password)
        
        # Otros campos
        for field, value in validated_data.items():
            if field == 'password':
                continue
            if value is not None and value != '' and value != []:
                setattr(instance, field, value)
        
        instance.save()
        return instance