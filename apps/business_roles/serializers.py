from rest_framework import serializers
from .models import BusinessPermission, BusinessRole, BusinessUser, BusinessUserRoleAssignment
from apps.authentication.serializers import UserSerializer

class BusinessPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPermission
        fields = ['id', 'code', 'name', 'module', 'description']

class BusinessRoleSerializer(serializers.ModelSerializer):
    permissions = BusinessPermissionSerializer(many=True, read_only=True)
    permission_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    permissions_count = serializers.SerializerMethodField()

    class Meta:
        model = BusinessRole
        fields = [
            'id', 'business', 'name', 'description', 'permissions', 
            'permission_codes', 'permissions_count', 'is_default', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'business', 'created_at', 'updated_at']

    def get_permissions_count(self, obj):
        return obj.permissions.count()

    def create(self, validated_data):
        permission_codes = validated_data.pop('permission_codes', [])
        role = super().create(validated_data)
        if permission_codes:
            perms = BusinessPermission.objects.filter(code__in=permission_codes)
            role.permissions.set(perms)
        return role


class BusinessUserRoleAssignmentSerializer(serializers.ModelSerializer):
    """Serializer para histórico de asignaciones"""
    business_user_id = serializers.UUIDField(write_only=True)
    role_id = serializers.UUIDField(write_only=True)
    role = BusinessRoleSerializer(read_only=True)
    assigned_by = UserSerializer(read_only=True)

    class Meta:
        model = BusinessUserRoleAssignment
        fields = [
            'id', 'business_user_id', 'role_id', 'role', 'assigned_by', 
            'assigned_at', 'revoked_at', 'is_active', 'notes'
        ]
        read_only_fields = ['id', 'assigned_at', 'revoked_at', 'assigned_by']


class BusinessUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    business_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    active_roles = serializers.SerializerMethodField()
    
    # Campos del usuario relacionados
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    
    # ✅ NUEVOS: Campos de contraseña
    password = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_blank=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = BusinessUser
        fields = [
            'id', 'user', 'user_id', 'business_id', 'employee_code', 
            'department', 'position', 'hire_date', 'is_active',
            'joined_at', 'left_at', 'active_roles', 'created_at', 'updated_at',
            'first_name', 'last_name', 'email',
            'password', 'password_confirm'  # ← AGREGAR
        ]
        read_only_fields = ['id', 'business_id', 'joined_at', 'left_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'employee_code': {'required': False, 'allow_blank': True},
            'department': {'required': False, 'allow_blank': True},
            'position': {'required': False, 'allow_blank': True},
            'hire_date': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({
                    'password': 'Las contraseñas no coinciden'
                })
            
            if len(password) < 6:
                raise serializers.ValidationError({
                    'password': 'La contraseña debe tener al menos 6 caracteres'
                })
        
        return attrs

    def get_active_roles(self, obj):
        assignments = obj.role_assignments.filter(is_active=True).select_related('role')
        return BusinessUserRoleAssignmentSerializer(assignments, many=True).data

