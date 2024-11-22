# calendars/admin.py
from django.contrib import admin
from .models import CalendarEvent, EventAttendee

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_datetime', 'end_datetime', 'created_by')
    list_filter = ('event_type', 'is_recurring')
    search_fields = ('title', 'description')

@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ('event', 'attendee', 'response_status')
    list_filter = ('response_status',)
    search_fields = ('attendee__username',)