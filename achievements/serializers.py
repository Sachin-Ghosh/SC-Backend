# achievements/serializers.py
from rest_framework import serializers
from .models import Achievement

class AchievementSerializer(serializers.ModelSerializer):
    achiever_name = serializers.CharField(source='achiever.username', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True)
    
    class Meta:
        model = Achievement
        fields = '__all__'
