# events/admin.py
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from .models import (
    Organization, Event, SubEvent, EventRegistration, 
    EventScore, EventDraw, SubEventImage, SubmissionFile
)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name', 'description')

@admin.register(Event)
class EventAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    list_display = ('name', 'event_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('event_type', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SubEvent)
class SubEventAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    list_display = ('name', 'event', 'category', 'schedule', 'registration_deadline')
    list_filter = ('category', 'event', 'participation_type')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('get_display_name', 'sub_event', 'registration_number', 'status', 'registration_date')
    list_filter = ('status', 'sub_event', 'department', 'year')
    search_fields = ('registration_number', 'team_name', 'team_leader__email', 'team_members__email')
    
    def get_display_name(self, obj):
        """Returns appropriate display name based on event type"""
        return obj.get_participant_display()
    get_display_name.short_description = 'Participant/Team'

    def get_fields(self, request, obj=None):
        """Dynamically show/hide fields based on event type"""
        fields = super().get_fields(request, obj)
        if obj and obj.sub_event.participation_type == 'SOLO':
            fields = [f for f in fields if f not in ['team_leader', 'team_name']]
        return fields

@admin.register(EventScore)
class EventScoreAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    list_display = ('sub_event', 'get_team_leader', 'total_score', 'judge', 'score_type')
    list_filter = ('sub_event', 'score_type', 'stage')
    search_fields = ('registration__team_leader__username', 'judge__username')

    def get_team_leader(self, obj):
        return obj.registration.team_leader.username
    get_team_leader.short_description = 'Team Leader'

@admin.register(EventDraw)
class EventDrawAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    list_display = ('sub_event', 'stage', 'team1', 'team2', 'winner', 'schedule')
    list_filter = ('sub_event', 'stage')
    search_fields = ('team1__team_leader__username', 'team2__team_leader__username')

@admin.register(SubEventImage)
class SubEventImageAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    list_display = ('caption', 'uploaded_at')
    search_fields = ('caption',)

@admin.register(SubmissionFile)
class SubmissionFileAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    list_display = ('registration', 'file_type', 'uploaded_at')
    list_filter = ('file_type',)
    search_fields = ('registration__team_leader__username',)