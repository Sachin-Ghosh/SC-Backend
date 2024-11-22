# events/admin.py
from django.contrib import admin
from .models import Event, SubEvent, EventRegistration, EventScore

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('event_type', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SubEvent)
class SubEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'category', 'schedule', 'registration_deadline')
    list_filter = ('category', 'event')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'sub_event', 'status', 'payment_status')
    list_filter = ('status', 'payment_status')
    search_fields = ('participant__username', 'team_name')

@admin.register(EventScore)
class EventScoreAdmin(admin.ModelAdmin):
    list_display = ('sub_event', 'participant', 'score', 'judge')
    list_filter = ('sub_event', 'department')
    search_fields = ('participant__username',)