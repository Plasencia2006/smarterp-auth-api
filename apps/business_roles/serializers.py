from rest_framework import serializers
from .models import BusinessPermission, BusinessRole

class BusinessPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPermission
        fields = ['id', 'code', 'name', 'module', 'description']

class BusinessRoleSerializer(serializers.ModelSerializer):
    permissions = BusinessPermissionSerializer(many=True, read_only=True)
    permission_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        label="Códigos de permisos"
    )

    class Meta:
        model = BusinessRole
        fields = ['id', 'business', 'name', 'description', 'permissions', 'permission_codes', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'business', 'created_at', 'updated_at']

    def validate_name(self, value):
        request = self.context.get('request')
        if request and hasattr(request.user, 'business'):
            if BusinessRole.objects.filter(business=request.user.business, name__iexact=value).exists():
                raise serializers.ValidationError("Ya existe un rol con ese nombre en este negocio.")
        return value

    def create(self, validated_data):
        permission_codes = validated_data.pop('permission_codes', [])
        role = super().create(validated_data)
        if permission_codes:
            perms = BusinessPermission.objects.filter(code__in=permission_codes)
            role.permissions.set(perms)
        return role

    def update(self, instance, validated_data):
        permission_codes = validated_data.pop('permission_codes', None)
        instance = super().update(instance, validated_data)
        if permission_codes is not None:
            perms = BusinessPermission.objects.filter(code__in=permission_codes)
            instance.permissions.set(perms)
        return instance