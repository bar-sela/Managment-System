from django.contrib.auth.password_validation import validate_password
from django.forms import ValidationError
from api import models as api_models

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import transaction
from userauths.models import Profile, User

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining a pair of access and refresh tokens.
    Extends the token payload with additional user information.
    """

    @classmethod
    def get_token(cls, user):
        """
        Override the default token generation method.
        Adds custom fields to the JWT token payload.

        Args:
            user (User): The authenticated user

        Returns:
            Token: The JWT token with custom payload
        """
        token = super().get_token(user)
        print(token)

        # Add custom claims
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username

        return token
      
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password]) # cheaks password not to short or too common ect
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'username',  'password', 'password2']
 
    def validate(self, attr): # called automatically during the is_valid
        if attr['password'] != attr['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attr  # returns the validate data 
    
    def create(self, validated_data):
        try:
            with transaction.atomic():
                # Create a new user instance
                user = User(
                    full_name=validated_data['full_name'],
                    email=validated_data['email'],
                    username=validated_data['username']
                )
                user.set_password(validated_data['password'])
                user.save()

            return user
        
        except Exception as e:
            # Handle any unexpected exceptions
            raise ValidationError({"detail": f"An unexpected error occurred: {str(e)}"})
  
        
    

class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password]) # insures password is enough hard

    class Meta:
        model = User
        fields = ['password', 'new_password', 'email']

    def validate(self, attrs):
        if attrs['password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": "New password must be different from the old password."})
        return attrs


    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"