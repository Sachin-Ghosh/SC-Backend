from django.shortcuts import render

# Create your views here.
# announcements/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Announcement
from .serializers import AnnouncementSerializer

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Announcement.objects.all()
        priority = self.request.query_params.get('priority', None)
        department = self.request.query_params.get('department', None)
        
        if priority:
            queryset = queryset.filter(priority=priority)
        if department:
            queryset = queryset.filter(departments__contains=department)
            
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_expired(self, request, pk=None):
        announcement = self.get_object()
        announcement.is_expired = True
        announcement.save()
        return Response({'status': 'announcement marked as expired'})