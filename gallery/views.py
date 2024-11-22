from django.shortcuts import render

# Create your views here.
# gallery/views.py
from rest_framework import viewsets, permissions
from .models import Album, Media
from .serializers import AlbumSerializer, MediaSerializer

class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [permissions.IsAuthenticated]

class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]