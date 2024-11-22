# gallery/serializers.py
from rest_framework import serializers
from .models import Album, Media

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'

class AlbumSerializer(serializers.ModelSerializer):
    media = MediaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Album
        fields = '__all__'