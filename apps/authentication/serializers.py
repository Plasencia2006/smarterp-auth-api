from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['username'] = user.username
        token['is_super_admin'] = user.is_super_admin
        token['estado'] = user.estado
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active_user:
            raise serializers.ValidationError(
                {'detail': 'Tu cuenta esta suspendida o inactiva.'}
            )
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'is_super_admin': self.user.is_super_admin,
        }
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Las contrasenas no coinciden.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


class UserDetailSerializer(serializers.ModelSerializer):
    memberships = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'estado', 'is_super_admin', 'date_joined', 'memberships']
        read_only_fields = fields

    def get_memberships(self, obj):
        from apps.business.serializers import MembershipSummarySerializer
        return MembershipSummarySerializer(
            obj.memberships.select_related('business').filter(is_active=True),
            many=True,
        ).data