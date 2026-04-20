from rest_framework import serializers
from .models import Business, Membership


class BusinessSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Business
        fields = ['id', 'name', 'type', 'owner', 'owner_email', 'is_active', 'created_at']
        read_only_fields = ['id', 'owner', 'owner_email', 'created_at']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user', 'user_email', 'business', 'business_name', 'role', 'is_active', 'joined_at']
        read_only_fields = ['id', 'user_email', 'business_name', 'joined_at']

    def validate(self, attrs):
        if Membership.objects.filter(user=attrs['user'], business=attrs['business']).exists():
            raise serializers.ValidationError('Este usuario ya tiene membresia en este negocio.')
        return attrs


class MembershipSummarySerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_type = serializers.CharField(source='business.type', read_only=True)

    class Meta:
        model = Membership
        fields = ['business_name', 'business_type', 'role']