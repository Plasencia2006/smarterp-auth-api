# apps/authentication/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


# =============================================================================
# ✅ 1. SERIALIZER PARA LOGIN (JWT) - CON MEMBRESÍAS
# =============================================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Login con JWT - Incluye datos del usuario y sus negocios asignados
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['username'] = user.username
        token['is_super_admin'] = getattr(user, 'is_super_admin', False) or user.is_superuser
        return token

    def validate(self, attrs):
        # Validar credenciales básicas
        data = super().validate(attrs)
        user = self.user
        
        # ✅ VALIDAR ESTADO DE LA CUENTA
        estado = getattr(user, 'estado', 'ACTIVO').upper()
        is_active = getattr(user, 'is_active', True)
        
        if not is_active:
            raise serializers.ValidationError({
                'detail': 'La cuenta está desactivada. Contacta al administrador.'
            })
        
        if estado == 'SUSPENDIDO':
            raise serializers.ValidationError({
                'detail': 'La cuenta está suspendida temporalmente.'
            })
        
        if estado == 'INACTIVO':
            raise serializers.ValidationError({
                'detail': 'La cuenta está inactiva. Contacta al administrador.'
            })
        
        if estado == 'ELIMINADO':
            raise serializers.ValidationError({
                'detail': 'Esta cuenta ha sido eliminada del sistema.'
            })
        
        # ✅ CONSULTAR MEMBRESÍAS DEL USUARIO (NEGOCIOS ASIGNADOS)
        try:
            from apps.business.models import Membership
            
            memberships = Membership.objects.filter(
                user=user,
                is_active=True
            ).select_related('business')
            
            # Serializar membresías
            memberships_data = []
            for m in memberships:
                memberships_data.append({
                    'id': str(m.id),
                    'business': str(m.business.id),  # ← CLAVE: debe ser 'business'
                    'business_name': m.business.name,
                    'role': m.role,
                    'is_active': m.is_active
                })
            
            print(f"✅ [Login] Usuario {user.email} tiene {len(memberships_data)} negocios asignados")
            
        except Exception as e:
            print(f"❌ [Login] Error al obtener membresías: {e}")
            memberships_data = []
        
        # ✅ CONSTRUIR RESPUESTA CON MEMBRESÍAS
        data['user'] = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_super_admin': getattr(user, 'is_super_admin', False) or user.is_superuser,
            'estado': estado,
            'is_active': is_active,
            # ✅ CAMPOS CLAVE PARA EL FRONTEND:
            'business_memberships': memberships_data,  # ← Prioritario
            'memberships': memberships_data,  # ← Fallback
        }
        
        return data


# =============================================================================
# ✅ 2. SERIALIZER PARA CREAR USUARIOS (REGISTRO)
# =============================================================================
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializador para crear nuevos usuarios.
    Hashea la contraseña automáticamente usando create_user.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'is_super_admin', 'estado'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


# =============================================================================
# ✅ 3. SERIALIZER PARA LISTAR USUARIOS (SOLO LECTURA)
# =============================================================================
class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para ver la lista de usuarios o detalles.
    NO incluye campos de escritura como password.
    """
    is_super_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'estado', 'is_super_admin', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'date_joined', 'last_login')

    def get_is_super_admin(self, obj):
        return getattr(obj, 'is_super_admin', False) or obj.is_superuser


# =============================================================================
# ✅ 4. SERIALIZER PARA DETALLE DE PERFIL (/me/)
# =============================================================================
class UserDetailSerializer(serializers.ModelSerializer):
    """Serializador para perfil del usuario actual"""
    is_super_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'estado', 'is_super_admin', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'date_joined', 'last_login')

    def get_is_super_admin(self, obj):
        return getattr(obj, 'is_super_admin', False) or obj.is_superuser


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