# users/serializers.py
from rest_framework import serializers
from .models import User, CouncilMember, Faculty
from django.conf import settings
from django.core.mail import send_mail
import random
import string

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'department', 'profile_picture', 
                 'bio', 'division', 'phone', 'roll_number', 'year_of_study', 'gender',
                 'id_card_document']
        extra_kwargs = {
            'password': {'write_only': True},
            'id_card_document': {'read_only': True}  # Only updatable through specific endpoints
        }

class CouncilMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CouncilMember
        fields = '__all__'

class FacultySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Faculty
        fields = '__all__'