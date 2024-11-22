from django.shortcuts import render

# Create your views here.
# resources/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ResourceCategory, Resource
from .serializers import ResourceCategorySerializer, ResourceSerializer

class ResourceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ResourceCategory.objects.all()
    serializer_class = ResourceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    @action(detail=True, methods=['post'])
    def increment_downloads(self, request, pk=None):
        resource = self.get_object()
        resource.download_count += 1
        resource.save()
        return Response({'download_count': resource.download_count})