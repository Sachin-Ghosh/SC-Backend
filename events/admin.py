# events/admin.py
from django.contrib import admin
from .models import (
    Organization, Event, SubEvent, EventRegistration, 
    EventScore, EventDraw, SubEventImage, SubmissionFile
)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name', 'description')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('event_type', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SubEvent)
class SubEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'category', 'schedule', 'registration_deadline')
    list_filter = ('category', 'event', 'participation_type')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'team_leader', 'sub_event', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'department', 'year', 'division')
    search_fields = ('registration_number', 'team_leader__username', 'team_name')

@admin.register(EventScore)
class EventScoreAdmin(admin.ModelAdmin):
    list_display = ('sub_event', 'get_team_leader', 'total_score', 'judge', 'score_type')
    list_filter = ('sub_event', 'score_type', 'stage')
    search_fields = ('registration__team_leader__username', 'judge__username')

    def get_team_leader(self, obj):
        return obj.registration.team_leader.username
    get_team_leader.short_description = 'Team Leader'

@admin.register(EventDraw)
class EventDrawAdmin(admin.ModelAdmin):
    list_display = ('sub_event', 'stage', 'team1', 'team2', 'winner', 'schedule')
    list_filter = ('sub_event', 'stage')
    search_fields = ('team1__team_leader__username', 'team2__team_leader__username')

@admin.register(SubEventImage)
class SubEventImageAdmin(admin.ModelAdmin):
    list_display = ('caption', 'uploaded_at')
    search_fields = ('caption',)

@admin.register(SubmissionFile)
class SubmissionFileAdmin(admin.ModelAdmin):
    list_display = ('registration', 'file_type', 'uploaded_at')
    list_filter = ('file_type',)
    search_fields = ('registration__team_leader__username',)