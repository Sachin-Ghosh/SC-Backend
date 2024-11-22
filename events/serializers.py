# events/serializers.py
from rest_framework import serializers
from .models import Event, SubEvent, EventRegistration, EventScore

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class SubEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubEvent
        fields = '__all__'

class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = '__all__'

class EventScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventScore
        fields = '__all__'