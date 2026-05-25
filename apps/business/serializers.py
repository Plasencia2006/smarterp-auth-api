# apps/business/serializers.py

from rest_framework import serializers
from .models import Business, Membership
from apps.authentication.serializers import UserSerializer


class BusinessSerializer(serializers.ModelSerializer):
    """Serializer para Negocios"""
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    total_members = serializers.SerializerMethodField()
    
    class Meta:
        model = Business
        fields = [
            'id', 'name', 'description', 'type',
            'email', 'phone', 'address',
            'owner', 'owner_name', 'owner_email',
            'is_active', 'total_members',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_members(self, obj):
        return obj.memberships.filter(is_active=True).count()
    
    def create(self, validated_data):
        if 'request' in self.context:
            validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer para Membresías"""
    user_details = UserSerializer(source='user', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = Membership
        fields = [
            'id', 'user', 'user_details',
            'business', 'business_name',
            'role', 'permissions', 'is_active', 
            'joined_at'
            # ❌ Eliminados: assigned_by, assigned_by_name
        ]
        read_only_fields = ['joined_at']
    
    def validate(self, attrs):
        if 'user' in attrs and 'business' in attrs:
            existing = Membership.objects.filter(
                user=attrs['user'],
                business=attrs['business'],
                is_active=True
            ).first()
            
            if existing and existing != self.instance:
                raise serializers.ValidationError(
                    f"Este usuario ya es {existing.get_role_display()} en este negocio."
                )
        
        return attrs


class AssignAdminSerializer(serializers.Serializer):
    """Serializer para asignar admin a negocio"""
    business_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=Membership.Role.choices, default='ADMIN')
    
    def validate(self, attrs):
        from django.contrib.auth import get_user_model
        
        try:
            Business.objects.get(id=attrs['business_id'])
        except Business.DoesNotExist:
            raise serializers.ValidationError("El negocio no existe.")
        
        try:
            get_user_model().objects.get(id=attrs['user_id'])
        except:
            raise serializers.ValidationError("El usuario no existe.")
        
        return attrs