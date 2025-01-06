# users/serializers.py
from rest_framework import serializers
from .models import User, CouncilMember, Faculty
from django.conf import settings
from django.core.mail import send_mail
import random
import string

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'user_type', 'department', 'profile_picture', 
                 'bio', 'division', 'phone', 'roll_number', 'year_of_study', 'gender',
                 'id_card_document']
        extra_kwargs = {
            'password': {'write_only': True},
            'id_card_document': {'read_only': True}  # Only updatable through specific endpoints
        }
        
    def get_full_name(self, obj):
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.username

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