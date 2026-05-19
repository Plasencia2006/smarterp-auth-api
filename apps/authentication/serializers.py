# apps/authentication/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


# ✅ 1. SERIALIZER PARA LOGIN (JWT)
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
        data = super().validate(attrs)
        user = self.user
        
        if not user.is_active or user.estado != 'ACTIVO':
             raise serializers.ValidationError({'detail': 'Cuenta desactivada o suspendida.'})
        
        data['user'] = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'is_super_admin': getattr(user, 'is_super_admin', False) or user.is_superuser,
        }
        return data


# ✅ 2. SERIALIZER PARA CREAR USUARIOS (CON PASSWORD)
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializador para crear nuevos usuarios.
    Hashea la contraseña automáticamente usando create_user.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'is_super_admin', 'estado')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # ✅ ESTO ES LO QUE GUARDA LA CONTRASEÑA:
        return User.objects.create_user(**validated_data)


# ✅ 3. SERIALIZER PARA LISTAR USUARIOS (SOLO LECTURA)
class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para ver la lista de usuarios o detalles.
    NO incluye campos de escritura como password.
    """
    is_super_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'estado', 'is_super_admin', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')

    def get_is_super_admin(self, obj):
        return getattr(obj, 'is_super_admin', False) or obj.is_superuser


# ✅ 4. SERIALIZER PARA DETALLE DE PERFIL (/me/)
class UserDetailSerializer(serializers.ModelSerializer):
    is_super_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'estado', 'is_super_admin', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')

    def get_is_super_admin(self, obj):
        return getattr(obj, 'is_super_admin', False) or obj.is_superuser


# ✅ 5. SERIALIZER PARA ACTUALIZAR USUARIOS (PERMITE EDICIÓN) ⭐ NUEVO
# ✅ 5. SERIALIZER PARA ACTUALIZAR USUARIOS (PERMITE EDICIÓN)
class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para actualizar usuarios.
    Maneja campos opcionales y validaciones flexibles.
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
        """
        Validar username: permitir espacios, pero verificar unicidad
        """
        if value == '' or value is None:
            # Si está vacío, mantener el valor actual
            return self.instance.username
        
        # Verificar que no exista otro usuario con este username
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        
        return value
    
    def validate_email(self, value):
        """
        Validar email: permitir vacío, pero validar formato si se proporciona
        """
        if value == '' or value is None:
            return self.instance.email
        
        # Validar formato de email
        from django.core.validators import validate_email
        try:
            validate_email(value)
        except:
            raise serializers.ValidationError("Ingresa un email válido.")
        
        return value
    
    def validate_password(self, value):
        """
        Ignorar password si está vacío
        """
        if value == '' or value is None:
            return None
        return value
    
    def update(self, instance, validated_data):
        """
        ✅ Actualiza solo los campos que tienen valores reales
        """
        # Password especial: solo actualizar si se proporcionó uno válido
        password = validated_data.get('password')
        if password and password.strip():
            instance.set_password(password)
        
        # Otros campos: actualizar solo si el valor no es None/vacío
        for field, value in validated_data.items():
            if field == 'password':
                continue
            # Solo actualizar si tiene un valor real (no None, no vacío, no lista vacía)
            if value is not None and value != '' and value != []:
                setattr(instance, field, value)
        
        instance.save()
        return instance
    
class UserUpdateSerializer(serializers.ModelSerializer):
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
            'username': {'required': False, 'allow_blank': False, 'max_length': 150},
            'email': {'required': False, 'allow_blank': True},
            'first_name': {'required': False, 'allow_blank': True, 'max_length': 150},
            'last_name': {'required': False, 'allow_blank': True, 'max_length': 150},
            'is_active': {'required': False},
            'is_super_admin': {'required': False},
            'estado': {'required': False},
        }
    
    def validate_username(self, value):
        """
        ✅ Validar username:
        - Solo permitir cambio si el usuario NUNCA ha iniciado sesión (last_login is None)
        - Verificar que no exista otro usuario con este username
        - Validar formato Django (sin espacios, solo @/./+/-/_)
        """
        # Si el valor no cambió, no validar
        if value == self.instance.username:
            return value
        
        # ✅ REGLA: Solo permitir cambiar username si NUNCA ha iniciado sesión
        if self.instance.last_login is not None:
            raise serializers.ValidationError(
                "El nombre de usuario solo puede modificarse una vez, antes del primer inicio de sesión."
            )
        
        # Verificar unicidad (excluyendo el usuario actual)
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        
        # Validar formato Django por defecto
        from django.core.validators import RegexValidator
        validator = RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='El nombre de usuario solo puede contener letras, números y @/./+/-/_'
        )
        try:
            validator(value)
        except:
            raise serializers.ValidationError(
                "El nombre de usuario solo puede contener letras, números y @/./+/-/_"
            )
        
        return value
    
    def validate_email(self, value):
        if value == '' or value is None:
            return self.instance.email
        from django.core.validators import validate_email
        try:
            validate_email(value)
        except:
            raise serializers.ValidationError("Ingresa un email válido.")
        return value
    
    def validate_password(self, value):
        if value == '' or value is None:
            return None
        return value
    
    def update(self, instance, validated_data):
        # Password especial
        password = validated_data.get('password')
        if password and password.strip():
            instance.set_password(password)
        
        # Actualizar campos
        for field, value in validated_data.items():
            if field == 'password':
                continue
            if value is not None and value != '' and value != []:
                setattr(instance, field, value)
        
        instance.save()
        return instance