# grievances/serializers.py
from rest_framework import serializers
from .models import Grievance, MediaFile

class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = '__all__'

class GrievanceSerializer(serializers.ModelSerializer):
    evidence = MediaFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Grievance
        fields = '__all__'