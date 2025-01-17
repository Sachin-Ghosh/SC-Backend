# events/models.py
from django.db import models
from django.conf import settings
from django.forms import ValidationError
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from users.models import CouncilMember
from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Avg

User = get_user_model()

class Organization(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    logo = models.ImageField(upload_to='organizations/')
    website = models.URLField(null=True, blank=True)
    
    def __str__(self):
        return self.name

class Event(models.Model):
    EVENT_TYPES = (
        ('INTRA', 'Intra College'),
        ('INTER', 'Inter College'),
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    event_type = models.CharField(max_length=5, choices=EVENT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    venue = models.CharField(max_length=200)
    max_participants = models.IntegerField()
    organizer = models.ForeignKey(CouncilMember, on_delete=models.CASCADE)
    collaborating_organizations = models.ManyToManyField(Organization, blank=True)
    chairpersons = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chaired_events',
        blank=True
    )
    vice_chairpersons = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='vice_chaired_events',
        blank=True
    )
    event_heads = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='headed_events',
        blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cover_image = models.ImageField(upload_to='events/')
    banner_image = models.ImageField(upload_to='events/banners/')
    rules_document = models.FileField(upload_to='events/rules/', null=True, blank=True)
    schedule_file = models.FileField(upload_to='events/schedules/', null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    # Social Media Links
    instagram_link = models.URLField(null=True, blank=True)
    facebook_link = models.URLField(null=True, blank=True)
    twitter_link = models.URLField(null=True, blank=True)
    linkedin_link = models.URLField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class EventCriteria(models.Model):
    CRITERIA_TYPES = (
        ('CULTURAL', 'Cultural Event'),
        ('SPORTS', 'Sports Event'),
        ('SPECIAL', 'Special Event')
    )
    
    name = models.CharField(max_length=100)
    event_type = models.CharField(max_length=20, choices=CRITERIA_TYPES)
    criteria = models.JSONField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Event Criteria"
    
    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()})"


class SubEvent(models.Model):
    EVENT_CATEGORIES = (
        ('SPORTS', 'Sports'),
        ('CULTURAL', 'Cultural'),
        ('TECHNICAL', 'Technical'),
        ('ACADEMIC', 'Academic')
    )
    
    GENDER_PARTICIPATION = (
        ('ALL', 'All'),
        ('MALE', 'Boys Only'),
        ('FEMALE', 'Girls Only')
    )
    
    PARTICIPATION_TYPES = (
        ('SOLO', 'Solo'),
        ('DUO', 'Duo'),
        ('GROUP', 'Group'),
    )
    
    EVENT_STAGES = (
        ('REGISTRATION', 'Registration'),
        ('PRELIMS', 'Preliminaries'),
        ('QUARTERS', 'Quarter Finals'),
        ('SEMIS', 'Semi Finals'),
        ('FINALS', 'Finals')
    )
    faculty_judges = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='SubEventFaculty',
        related_name='judged_sub_events',
        blank=True
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sub_events')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    short_description = models.TextField(null=True , blank=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=EVENT_CATEGORIES , null=True , blank=True)
    participation_type = models.CharField(max_length=10, choices=PARTICIPATION_TYPES , null=True , blank=True)
    current_stage = models.CharField(max_length=20, choices=EVENT_STAGES, default='REGISTRATION' , null=True , blank=True)
    schedule = models.DateTimeField(null=True , blank=True)
    venue = models.CharField(max_length=200 , null=True , blank=True)
    max_participants = models.IntegerField(null=True , blank=True)
    min_team_size = models.IntegerField(default=1 , null=True , blank=True)
    max_team_size = models.IntegerField(default=1 , null=True , blank=True)
    registration_deadline = models.DateTimeField(null=True , blank=True)
    sub_heads = models.ManyToManyField(
        'users.User',
        related_name='managed_sub_events',
        blank=True,
        limit_choices_to={'user_type': 'COUNCIL', 'is_active': True},
        help_text="Select council members who will manage this sub-event"
    )
    gender_participation = models.CharField(
        max_length=10,
        choices=GENDER_PARTICIPATION,
        default='ALL',
        help_text='Specify if the event is open to all or restricted by gender',
        null=True , blank=True
    )
    registration_fee = models.DecimalField(max_digits=8, decimal_places=2 , null=True , blank=True)
    rules = models.TextField(null=True , blank=True)
    scoring_criteria = models.ForeignKey(
        EventCriteria, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True
    )
    prize_pool = models.DecimalField(max_digits=10, decimal_places=2 , null=True , blank=True)
    prize_pool_description = models.TextField(null=True , blank=True)
    format_description = models.TextField(null=True , blank=True)
    allow_mixed_department = models.BooleanField(default=False)
    allow_mixed_year = models.BooleanField(default=False)
    allow_mixed_division = models.BooleanField(default=False)
    double_trouble_allowed = models.BooleanField(default=False)
    upload_link = models.BooleanField(default=False)
    images = models.ManyToManyField(
        'SubEventImage',
        related_name='sub_events',
        blank=True
    )
    
    ROUND_FORMATS = (
        ('ELIMINATION', 'Elimination'),  # Participants get eliminated each round
        ('POINTS', 'Points Based'),      # Points accumulate across rounds
        ('TIME', 'Time Based'),          # Best time/score counts
    )
    
    round_format = models.CharField(max_length=20, choices=ROUND_FORMATS , null=True , blank=True)
    participants_per_group = models.IntegerField(default=5 , null=True , blank=True)  # How many compete at once
    qualifiers_per_group = models.IntegerField(default=3 , null=True , blank=True)   # How many advance
    current_round = models.IntegerField(default=1 , null=True , blank=True)
    total_rounds = models.IntegerField(default=1 , null=True , blank=True)
    registration_start_time = models.DateTimeField(null=True, blank=True)
    registration_end_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    reporting_time = models.TimeField(null=True, blank=True)
    
    # Add new fields for event-specific scoring
    SCORING_TYPES = (
        ('STANDARD', 'Standard Scoring'),
        ('SPORTS_GROUP', 'Sports Group Event'),
        ('SPORTS_SOLO', 'Sports Solo Event'),
        ('CULTURAL_GROUP', 'Cultural Group Event'),
        ('CULTURAL_SOLO', 'Cultural Solo Event'),
        ('SPECIAL', 'Special Event')  # For events like Fashion Show, Mr/Ms Aurora
    )
    
    scoring_type = models.CharField(max_length=20, choices=SCORING_TYPES, default='STANDARD' , null=True , blank=True)
    aura_points_winner = models.IntegerField(default=200 , null=True , blank=True)
    aura_points_runner = models.IntegerField(default=100 , null=True , blank=True)
    match_points_enabled = models.BooleanField(default=False , null=True , blank=True)
    allow_joint_winners = models.BooleanField(default=False , null=True , blank=True)
    allow_negative_marking = models.BooleanField(default=False , null=True , blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_active_faculty(self):
        return self.faculty_judges.filter(is_active=True)
    
    def __str__(self):
        return f"{self.event.name} - {self.name}"

    def get_scoring_criteria(self):
        """Return scoring criteria for the event"""
        if not self.scoring_criteria:
            return {}
        return self.scoring_criteria.criteria

    def update_stage(self, new_stage):
        """Update event stage with validation"""
        valid_transitions = {
            'PENDING': ['REGISTRATION'],
            'REGISTRATION': ['ONGOING', 'CANCELLED'],
            'ONGOING': ['SCORING', 'CANCELLED'],
            'SCORING': ['COMPLETED', 'CANCELLED'],
            'COMPLETED': ['ARCHIVED'],
            'CANCELLED': ['ARCHIVED'],
            'ARCHIVED': []
        }
        
        if new_stage not in valid_transitions.get(self.current_stage, []):
            raise ValidationError(
                f"Invalid stage transition from {self.current_stage} to {new_stage}"
            )
        
        self.current_stage = new_stage
        self.save()
        
        # Trigger stage-specific actions
        if new_stage == 'ONGOING':
            self._notify_participants()
        elif new_stage == 'SCORING':
            self._notify_judges()
        elif new_stage == 'COMPLETED':
            self._finalize_results()
    
    def _notify_participants(self):
        """Notify participants when event starts"""
        registrations = self.eventregistration_set.filter(status='APPROVED')
        for registration in registrations:
            # Send email notification
            context = {
                'participant': registration.user.get_full_name(),
                'event': self.name,
                'venue': self.venue,
                'schedule': self.schedule
            }
            send_mail(
                subject=f'{self.name} is starting soon!',
                message=render_to_string('events/emails/event_starting.txt', context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[registration.user.email]
            )
    
    def _notify_judges(self):
        """Notify faculty when scoring starts"""
        faculty_assignments = self.faculty_assignments.filter(is_active=True)
        for assignment in faculty_assignments:
            context = {
                'faculty': assignment.faculty.get_full_name(),
                'event': self.name,
                'scoring_link': f'/events/scoring/{self.id}/'
            }
            send_mail(
                subject=f'Scoring open for {self.name}',
                message=render_to_string('events/emails/scoring_open.txt', context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[assignment.faculty.email]
            )
    
    def _finalize_results(self):
        """Finalize results and calculate AURA points"""
        scores = EventScore.objects.filter(sub_event=self)
        
        # Calculate average scores per registration
        avg_scores = scores.values(
            'event_registration'
        ).annotate(
            avg_score=Avg('total_score')
        ).order_by('-avg_score')
        
        # Assign positions and AURA points
        for idx, score in enumerate(avg_scores, 1):
            registration = EventRegistration.objects.get(
                id=score['event_registration']
            )
            
            if idx == 1:  # Winner
                aura_points = self.aura_points_winner
            elif idx == 2:  # Runner-up
                aura_points = self.aura_points_runner
            else:
                continue
            
            DepartmentScore.record_score(registration, self, aura_points)

class SubEventImage(models.Model):
    sub_event = models.ForeignKey(
        'SubEvent',
        related_name='image_set',
        on_delete=models.CASCADE,
        null=True,  # Allow null temporarily for migration
        blank=True
    )
    image = models.ImageField(upload_to='sub_events/images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if hasattr(self, 'sub_event') and self.sub_event:
            return f"Image for {self.sub_event.name}"
        return f"Image {self.id}" if self.id else "New Image"
   
class SubEventFaculty(models.Model):
    sub_event = models.ForeignKey(
        SubEvent, 
        on_delete=models.CASCADE,
        related_name='faculty_assignments'
    )
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'FACULTY'}
    )
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ['sub_event', 'faculty']
        verbose_name_plural = "Sub Event Faculty"
    
    def __str__(self):
        return f"{self.faculty.get_full_name()} - {self.sub_event.name}"
    
    def clean(self):
        if self.faculty.user_type != 'FACULTY':
            raise ValidationError("Only faculty members can be assigned as judges")

class EventRegistration(models.Model):
    REGISTRATION_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('DISQUALIFIED', 'Disqualified')
    )
    
    DEPARTMENT_TYPES = (
        ('AS&H','AS&H'),
        ('COMPUTER', 'Comps'),
        ('IT', 'IT'),
        ('AIML', 'AIML'),
        ('DE', 'DE'),
        ('CIVIL', 'Civil'),
        ('OTHER', 'Other')
    )
    DIVISION_TYPES = (
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
        ('F', 'F')
    )
    YEAR_TYPES = (
        ('FE', 'FE'),
        ('SE', 'SE'),
        ('TE', 'TE'),
        ('BE', 'BE')
    )
    
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    team_leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='led_registrations' , null=True , blank=True
    )
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='team_registrations',
        blank=True 
    )
    team_name = models.CharField(max_length=100, null=True, blank=True)
    registration_number = models.CharField(
        max_length=20, 
        unique=True,
        null=True,  # Allow null temporarily for migration
        blank=True  # Allow blank temporarily for migration
    )
    department = models.CharField(max_length=100, choices=DEPARTMENT_TYPES , null=True , blank=True)
    year = models.CharField(max_length=10 , choices=YEAR_TYPES , null=True , blank=True)
    division = models.CharField(max_length=10 , choices=DIVISION_TYPES , null=True , blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='PENDING')
    payment_status = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_stage = models.CharField(max_length=20, choices=SubEvent.EVENT_STAGES, default='REGISTRATION')
    has_submitted_files = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_participant_display(self):
        """Returns display text based on event type and participants"""
        if self.sub_event.participation_type == 'SOLO':
            participant = self.team_members.first()
            if participant:
                return f"{participant.first_name} {participant.last_name}"
            return "No participant assigned"
        else:
            if self.team_name:
                return self.team_name
            return "Unnamed Team"

    def __str__(self):
        """Dynamic string representation based on event type"""
        if self.sub_event.participation_type == 'SOLO':
            participant = self.team_members.first()
            if participant:
                return f"{participant.first_name} {participant.last_name} - {self.sub_event.name}"
            return f"Unassigned - {self.sub_event.name}"
        else:
            team_name = self.team_name or "Unnamed Team"
            return f"{team_name} - {self.sub_event.name}"

    def get_primary_contact(self):
        """Returns the primary contact person for the registration"""
        if self.team_leader:
            return self.team_leader
        return self.team_members.first()

    def get_all_participants(self):
        """Returns all participants including the team leader"""
        return self.team_members.all()

    def save(self, *args, **kwargs):
        # Generate registration number if not exists
        if not self.registration_number:
            prefix = f"{self.sub_event.event.name[:3]}{self.sub_event.name[:3]}".upper()
            timestamp = timezone.now().strftime('%Y%m%d%H%M')
            self.registration_number = f"{prefix}{timestamp}"
        
        # For solo events, ensure no team leader is set
        if self.sub_event.participation_type == 'SOLO':
            self.team_leader = None
            self.team_name = None
        
        super().save(*args, **kwargs)

class SubmissionFile(models.Model):
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='submissions/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'mp4', 'mov'])]
    )
    file_type = models.CharField(max_length=10)  # 'image' or 'video'
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission for {self.registration}"

class EventDraw(models.Model):
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    stage = models.CharField(max_length=20, choices=SubEvent.EVENT_STAGES)
    team1 = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='team1_draws'
    )
    team2 = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='team2_draws'
    )
    winner = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='won_draws',
        null=True,
        blank=True
    )
    schedule = models.DateTimeField()
    venue = models.CharField(max_length=200)
    
    class Meta:
        unique_together = ['sub_event', 'stage', 'team1', 'team2']

    def __str__(self):
        return f"{self.sub_event.name} - {self.stage} - {self.team1} vs {self.team2}"

class EventHeat(models.Model):
    HEAT_STATUS = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    )
    
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE , null=True , blank=True)
    stage = models.CharField(max_length=20, choices=SubEvent.EVENT_STAGES , null=True , blank=True)
    round_number = models.IntegerField( null=True , blank=True)
    heat_number = models.IntegerField( default=1 , blank=True)
    schedule = models.DateTimeField( null=True , blank=True)
    venue = models.CharField(max_length=100 , null=True , blank=True)
    max_participants = models.IntegerField( null=True , blank=True)
    status = models.CharField(max_length=20, choices=HEAT_STATUS, default='PENDING' , null=True , blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True , null=True , blank=True)
    updated_at = models.DateTimeField(auto_now=True , null=True , blank=True)
    
    class Meta:
        unique_together = ['sub_event', 'stage', 'round_number', 'heat_number']
        ordering = ['round_number', 'heat_number']
    
    def __str__(self):
        return f"{self.sub_event.name} - {self.stage} Round {self.round_number} Heat {self.heat_number}"
    
    def clean(self):
        if self.schedule < timezone.now():
            raise ValidationError("Schedule cannot be in the past")
        if self.max_participants < 2:
            raise ValidationError("Heat must have at least 2 participants")

class HeatParticipant(models.Model):
    heat = models.ForeignKey(EventHeat, on_delete=models.CASCADE)
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE)
    position = models.IntegerField(null=True, blank=True)
    qualified_for_next = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ['heat', 'registration']
    
    def __str__(self):
        return f"{self.registration.get_participant_display()} - Heat {self.heat.heat_number}"

class EventScore(models.Model):
    SCORE_TYPES = (
        ('WINNER', 'Winner'),
        ('RUNNER_UP', 'Runner Up'),
        ('JOINT_WINNER', 'Joint Winner'),
        ('PARTICIPANT', 'Participant')
    )
    
    EVENT_TYPES = (
        ('SPORTS', 'Sports'),
        ('CULTURAL', 'Cultural'),
        ('SPECIAL', 'Special')  # For events like Mr/Ms Aurora
    )
    
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    event_registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE,
        related_name='scores')
    stage = models.CharField(max_length=20, choices=SubEvent.EVENT_STAGES, null=True, blank=True)
    score_type = models.CharField(max_length=20, choices=SCORE_TYPES, null=True, blank=True)
    
    # For cultural events scoring
    criteria_scores = models.JSONField(default=dict, null=True, blank=True)
    total_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    negative_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # AURA points
    aura_points = models.IntegerField(default=0)
    match_points = models.IntegerField(default=0)  # For sports group events (20 points per match)
    is_bye = models.BooleanField(default=False)
    
    remarks = models.TextField(null=True, blank=True)
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='judged_scores', null=True, blank=True)
    
    heat = models.ForeignKey(EventHeat, on_delete=models.CASCADE, null=True, blank=True)
    round_number = models.IntegerField(null=True, blank=True)
    position = models.IntegerField(null=True)
    qualified_for_next = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Calculate final score considering negative marking
        if self.criteria_scores:
            self.total_score = sum(self.criteria_scores.values()) - self.negative_marks
        
        # Auto-calculate AURA points based on event type and position
        if self.score_type and not self.is_bye:
            self._calculate_aura_points()
            
        super().save(*args, **kwargs)
        self._update_department_score()
    
    def _calculate_aura_points(self):
        # """Calculate AURA points based on event type and position"""
        event_type = self.sub_event.category
        participation_type = self.sub_event.participation_type
        
        # Define points mapping
        points_map = {
            'SPORTS': {
                'GROUP': {'WINNER': 400, 'RUNNER_UP': 200},
                'SOLO': {'WINNER': 200, 'RUNNER_UP': 100}
            },
            'CULTURAL': {
                'GROUP': {'WINNER': 400, 'RUNNER_UP': 200},
                'SOLO': {'WINNER': 200, 'RUNNER_UP': 100}
            }
        }
        
        # Special cases
        special_events = {
            'CRICKET': {'WINNER': 600, 'RUNNER_UP': 300},
            'FASHION_SHOW': {'WINNER': 500, 'RUNNER_UP': 250},
            'MR_MS_AURORA': {'WINNER': 600, 'RUNNER_UP': 300},
            'TRACK_FIELD': {'WINNER': 500, 'RUNNER_UP': 250}
        }

    def __str__(self):
        participant = self.event_registration.get_participant_display()
        return f"{participant} - {self.sub_event.name} - {self.stage}"

    def save(self, *args, **kwargs):
        if self.heat and not self.round_number:
            self.round_number = self.heat.round_number
        super().save(*args, **kwargs)
        
        # Update department scores if this is a winning score
        if self.score_type in ['WINNER', 'RUNNER_UP']:
            self._update_department_score()
    
    def _update_department_score(self):
        registration = self.event_registration
        
        # Get total_score from EventScore
        total_score = self.total_score if self.total_score else 0
        
        dept_score, created = DepartmentScore.objects.get_or_create(
            department=registration.department,
            year=registration.year,
            division=registration.division,
            sub_event=self.sub_event,
            defaults={
                'total_score': total_score,  # Set the total_score
                'aura_points': self.aura_points,
                'updated_at': timezone.now()
            }
        )
        
        if not created:
            # Update existing score
            dept_score.total_score = total_score
            dept_score.aura_points = self.aura_points
            dept_score.save()

    def add_match_points(self):
        """Add 20 points for winning matches in group sports events"""
        if (self.sub_event.category == 'SPORTS' and 
            self.sub_event.participation_type == 'GROUP' and 
            self.stage != 'FINALS' and 
            self.score_type == 'WINNER' and 
            not self.is_bye):
            self.match_points = 20
            self.save()

class DepartmentScore(models.Model):
    department = models.CharField(max_length=50)
    year = models.CharField(max_length=10, null=True, blank=True)  # Nullable for Civil
    division = models.CharField(max_length=10, null=True, blank=True)  # Nullable for Civil
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    total_score = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0  # Add default value
    )
    aura_points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Special handling for Civil department
        if self.department == 'CIVIL':
            self.year = None
            self.division = None
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.department} {self.year} {self.division} - {self.sub_event.name}"
    
    @classmethod
    def update_civil_scores(cls, sub_event_id):
        """Update scores for Civil department by combining all years/divisions"""
        civil_scores = cls.objects.filter(
            department='CIVIL',
            sub_event_id=sub_event_id
        )
        
        total_aura_points = civil_scores.aggregate(
            total=Sum('aura_points')
        )['total'] or 0
        
        # Create or update combined score
        cls.objects.update_or_create(
            department='CIVIL',
            sub_event_id=sub_event_id,
            year=None,
            division=None,
            defaults={
                'aura_points': total_aura_points,
                'updated_at': timezone.now()
            }
        )
        
        # Delete individual year/division scores
        civil_scores.exclude(
            year__isnull=True,
            division__isnull=True
        ).delete()
    
    @classmethod
    def record_score(cls, registration, sub_event, aura_points):
        """Record score for a registration, handling Civil department specially"""
        if registration.department == 'CIVIL':
            # Create temporary score
            score = cls.objects.create(
                department='CIVIL',
                sub_event=sub_event,
                year=registration.year,
                division=registration.division,
                aura_points=aura_points
            )
            # Update combined Civil score
            cls.update_civil_scores(sub_event.id)
        else:
            # Normal department scoring
            score = cls.objects.create(
                department=registration.department,
                year=registration.year,
                division=registration.division,
                sub_event=sub_event,
                aura_points=aura_points
            )
        return score
    
    
class DepartmentTotal(models.Model):
    department = models.CharField(max_length=50)
    year = models.CharField(max_length=10, null=True, blank=True)
    division = models.CharField(max_length=10, null=True, blank=True)
    total_aura_points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['department', 'year', 'division']
    
    