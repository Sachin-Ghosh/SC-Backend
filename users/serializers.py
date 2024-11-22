# users/serializers.py
from rest_framework import serializers
from .models import User, CouncilMember, Faculty

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'department', 'profile_picture', 
                 'bio', 'division', 'phone', 'roll_number', 'year_of_study']
        extra_kwargs = {'password': {'write_only': True}}

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