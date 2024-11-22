from django.shortcuts import render

# Create your views here.
# calendar/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, timedelta
from .models import CalendarEvent, EventAttendee
from .serializers import CalendarEventSerializer, EventAttendeeSerializer

class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = CalendarEvent.objects.all()
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        event_type = self.request.query_params.get('event_type', None)

        if start_date:
            queryset = queryset.filter(start_datetime__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_datetime__lte=end_date)
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        return queryset

    @action(detail=True, methods=['post'])
    def update_attendance(self, request, pk=None):
        event = self.get_object()
        attendee, created = EventAttendee.objects.get_or_create(
            event=event,
            attendee=request.user,
            defaults={'response_status': request.data.get('status', 'PENDING')}
        )
        if not created:
            attendee.response_status = request.data.get('status')
            attendee.save()
        return Response({'status': 'attendance updated'})