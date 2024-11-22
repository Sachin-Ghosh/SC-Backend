# resources/serializers.py
from rest_framework import serializers
from .models import ResourceCategory, Resource

class ResourceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceCategory
        fields = '__all__'

class ResourceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Resource
        fields = '__all__'