from .models import Profile,Account,Land
from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_verified']
        
class ProfileSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    class Meta:
        model = Profile
        fields = '__all__'

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for attr in ['first_name', 'last_name', 'username', 'email']:
                if attr in user_data:
                    setattr(user, attr, user_data[attr])
            user.save()
        # Update other profile fields if needed
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # Explicitly allow updating birth_date
        if 'birth_date' in validated_data:
            instance.birth_date = validated_data['birth_date']
        instance.save()
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id','username', 'email', 'password', 'first_name', 'last_name', 'is_verified','verification_token']
        read_only_fields = ['is_verified','verification_token']
    def is_valid(self,raise_exception=False):
        valid = super().is_valid(raise_exception=raise_exception)
        if valid:
            username = self.validated_data["username"]
            if Account.objects.filter(username=username).exists():
                self._errors["username"] = "Username already exists"
                valid =  False
        return valid
    def create(self, validated_data):
        user = Account.objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        # verification_link = f"{settings.SITE_URL}/verify-email/{user.verification_token}"
        # send_mail(
        #     'Verify your email',
        #     f'Click this link to verify your email: {verification_link}',
        #     settings.DEFAULT_FROM_EMAIL,
        #     [user.email],
        #     fail_silently=False,
        # )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['is_verified'] = self.user.is_verified
        return data


class LandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Land
        fields = '__all__'
        extra_kwargs = {
            'land_user': {'required': False}
        }