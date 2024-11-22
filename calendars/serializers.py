from rest_framework import serializers
from .models import CalendarEvent, EventAttendee

class EventAttendeeSerializer(serializers.ModelSerializer):
    attendee_name = serializers.CharField(source='attendee.username', read_only=True)
    
    class Meta:
        model = EventAttendee
        fields = '__all__'

class CalendarEventSerializer(serializers.ModelSerializer):
    attendees = EventAttendeeSerializer(many=True, read_only=True)
    
    class Meta:
        model = CalendarEvent
        fields = '__all__'