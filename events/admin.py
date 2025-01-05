# events/admin.py
from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from django_summernote.admin import SummernoteModelAdmin

from .models import (
    Organization, Event, SubEvent, EventRegistration, 
    EventScore, EventDraw, SubEventImage, SubmissionFile,
    SubEventFaculty, EventHeat, DepartmentScore
)

class SubEventFacultyInline(admin.TabularInline):
    model = SubEventFaculty
    extra = 1
    raw_id_fields = ('faculty',)
    autocomplete_fields = ['faculty']
    fields = ('faculty', 'is_active', 'remarks')


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
    list_display = ('name', 'event', 'category', 'participation_type', 'current_stage', 'get_faculty_count')
    list_filter = ('event', 'category', 'participation_type', 'current_stage')
    search_fields = ('name', 'event__name')
    inlines = [SubEventFacultyInline]
    
    def get_faculty_count(self, obj):
        # Changed from subeventfaculty to faculty_assignments (the related_name we defined)
        return obj.faculty_assignments.filter(is_active=True).count()
    get_faculty_count.short_description = 'Active Faculty Count'

    fieldsets = (
        ('Basic Information', {
            'fields': ('event', 'name', 'slug', 'short_description', 'description')
        }),
        ('Event Details', {
            'fields': (
                'category', 'participation_type', 'current_stage',
                'schedule', 'venue', 'max_participants',
                'min_team_size', 'max_team_size'
            )
        }),
        ('Registration', {
            'fields': (
                'registration_deadline', 'registration_fee',
                'registration_start_time', 'registration_end_time'
            )
        }),
        ('Event Format', {
            'fields': (
                'round_format', 'participants_per_group',
                'qualifiers_per_group', 'current_round',
                'total_rounds', 'date', 'reporting_time'
            )
        }),
        ('Rules & Criteria', {
            'fields': (
                'rules', 'scoring_criteria', 'prize_pool',
                'prize_pool_description', 'format_description'
            )
        }),
        ('Participation Rules', {
            'fields': (
                'gender_participation',
                'allow_mixed_department', 'allow_mixed_year',
                'allow_mixed_division', 'double_trouble_allowed'
            )
        })
    )
    
@admin.register(SubEventFaculty)
class SubEventFacultyAdmin(admin.ModelAdmin):
    list_display = ('faculty_name', 'sub_event_name', 'is_active', 'assigned_at')
    list_filter = ('is_active', 'sub_event', 'faculty')
    search_fields = ('faculty__first_name', 'faculty__last_name', 'sub_event__name')
    autocomplete_fields = ['faculty', 'sub_event']

    def faculty_name(self, obj):
        return obj.faculty.get_full_name()
    faculty_name.short_description = 'Faculty'

    def sub_event_name(self, obj):
        return obj.sub_event.name
    sub_event_name.short_description = 'Sub Event'

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
class EventScoreAdmin(admin.ModelAdmin):
    list_display = ('get_participant', 'get_event_name', 'stage', 'total_score', 'position', 'qualified_for_next')
    list_filter = ('sub_event', 'stage', 'qualified_for_next')
    search_fields = ('event_registration__team_name', 'sub_event__name')
    readonly_fields = ('updated_at',)

    def get_participant(self, obj):
        if obj.event_registration:
            return obj.event_registration.get_participant_display()
        return "No participant"
    get_participant.short_description = 'Participant/Team'

    def get_event_name(self, obj):
        return f"{obj.sub_event.name}"
    get_event_name.short_description = 'Event'

    fieldsets = (
        ('Event Information', {
            'fields': ('sub_event', 'event_registration', 'stage')
        }),
        ('Score Details', {
            'fields': ('score_type', 'total_score', 'criteria_scores', 'position')
        }),
        ('Heat Information', {
            'fields': ('heat', 'round_number', 'time_taken')
        }),
        ('Status', {
            'fields': ('qualified_for_next', 'is_bye', 'points_awarded')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'judge', 'updated_by', 'updated_at')
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sub_event',
            'event_registration',
            'judge',
            'updated_by',
            'heat'
        )
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
    
@admin.register(EventHeat)
class EventHeatAdmin(admin.ModelAdmin):
    list_display = ('get_heat_display', 'status', 'scheduled_time', 'get_participant_count')
    list_filter = ('sub_event', 'round_number', 'status')
    search_fields = ('sub_event__name', 'notes')
    readonly_fields = ('completed_time',)
    
    def get_heat_display(self, obj):
        return f"{obj.sub_event.name} - Round {obj.round_number} Heat {obj.heat_number}"
    get_heat_display.short_description = 'Event Heat'

    def get_participant_count(self, obj):
        return obj.participants.count()
    get_participant_count.short_description = 'Participants'

    fieldsets = (
        ('Event Information', {
            'fields': ('sub_event', 'round_number', 'heat_number')
        }),
        ('Status & Schedule', {
            'fields': ('status', 'scheduled_time', 'completed_time')
        }),
        ('Participants', {
            'fields': ('participants',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sub_event')
    

@admin.register(DepartmentScore)
class DepartmentScoreAdmin(admin.ModelAdmin):
    list_display = ('department', 'year', 'division', 'sub_event', 'points', 'updated_at')
    list_filter = ('department', 'year', 'division', 'sub_event__event')
    search_fields = ('department', 'sub_event__name')
    readonly_fields = ('updated_at',)
    change_list_template = 'admin/scoreboard_change_list.html'  # Use custom template
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = self.get_queryset(request)
            
            # Get all sub events
            sub_events = SubEvent.objects.all().order_by('name')
            
            # Get all unique class groups (year-department-division combinations)
            class_groups = qs.values(
                'year', 'department', 'division'
            ).annotate(
                total_points=Sum('points')
            ).order_by('department', 'year', 'division')
            
            # Get scores matrix
            scores = {}
            for score in qs:
                if score.sub_event_id not in scores:
                    scores[score.sub_event_id] = {}
                key = f"{score.year}_{score.department}_{score.division}"
                scores[score.sub_event_id][key] = score.points
            
            extra_context = {
                'sub_events': sub_events,
                'class_groups': class_groups,
                'scores': scores,
                'total_points': qs.aggregate(Sum('points'))['points__sum'] or 0,
            }
            response.context_data.update(extra_context)
        except:
            pass
        
        return response

    class Media:
        css = {
            'all': ('admin/css/scoreboard.css',)
        }

# Create a proxy model for the scoreboard view
class Scoreboard(DepartmentScore):
    class Meta:
        proxy = True
        verbose_name = 'Scoreboard'
        verbose_name_plural = 'Scoreboard'

@admin.register(Scoreboard)
class ScoreboardAdmin(admin.ModelAdmin):
    change_list_template = 'admin/scoreboard_change_list.html'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        scores = DepartmentScore.objects.all()
        
        # Department-wise totals
        department_totals = scores.values('department').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
        
        # Year-wise totals
        year_totals = scores.values('year').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
        
        # Division-wise totals
        division_totals = scores.values('division').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
        
        # Combined totals
        combined_totals = scores.values(
            'department', 'year', 'division'
        ).annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
        
        extra_context = {
            'department_totals': department_totals,
            'year_totals': year_totals,
            'division_totals': division_totals,
            'combined_totals': combined_totals,
        }
        
        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        css = {
            'all': ('admin/css/scoreboard.css',)
        }