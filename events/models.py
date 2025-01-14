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
        settings.AUTH_USER_MODEL,
        related_name='sub_headed_events' , blank=True
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
    scoring_criteria = models.JSONField(default=dict , null=True , blank=True)  # Store judging criteria
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
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_active_faculty(self):
        return self.faculty_judges.filter(is_active=True)
    
    def __str__(self):
        return f"{self.event.name} - {self.name}"


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
    # Change the faculty field to point to User model
    faculty = models.ForeignKey(
        User,  # Use User model directly
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'FACULTY'}  # Optional: limit to faculty users
    )
    sub_event = models.ForeignKey(
        SubEvent, 
        on_delete=models.CASCADE,
        related_name='faculty_assignments'  # Add this line
    )
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ['sub_event', 'faculty']
        # verbose_name = 'Sub Event Faculty'
        # verbose_name_plural = 'Sub Event Faculties'

    def __str__(self):
        # return f"{self.faculty.get_full_name()} - {self.sub_event.name}"
        return f"{self.faculty.email} - {self.sub_event.name}"
    
    
class EventRegistration(models.Model):
    REGISTRATION_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
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
        ('COMPLETED', 'Completed')
    )
    
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    heat_name = models.CharField(max_length=100 , null=True , blank=True)
    stage = models.CharField(max_length=50, null=True, blank=True)
    round_number = models.IntegerField(default=1, null=True, blank=True)
    schedule = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=200, null=True, blank=True)
    max_participants = models.IntegerField(default=0, null=True, blank=True)
    status = models.CharField(max_length=20, choices=HEAT_STATUS,
        default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['stage', 'round_number', 'created_at']

    def __str__(self):
        return f"Heat {self.round_number} - {self.sub_event.name} ({self.stage})"
    def clean(self):
        if self.max_participants <= 0:
            raise ValidationError('Maximum participants must be greater than 0')

class HeatParticipant(models.Model):
    heat = models.ForeignKey(EventHeat, on_delete=models.CASCADE)
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['heat', 'registration']

    def __str__(self):
        return f"{self.registration} - Heat {self.heat.round_number}"

class EventScore(models.Model):
    SCORE_TYPES = (
        ('WINNER', 'Winner'),
        ('RUNNER_UP', 'Runner Up'),
        ('PARTICIPANT', 'Participant')
    )
    
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    event_registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE,
        related_name='scores')  # Changed from registration to event_registration
    stage = models.CharField(max_length=20, choices=SubEvent.EVENT_STAGES , null=True , blank=True)
    score_type = models.CharField(max_length=20, choices=SCORE_TYPES, null=True, blank=True)
    criteria_scores = models.JSONField(default=dict , null=True , blank=True)
    total_score = models.DecimalField(max_digits=8, decimal_places=2 , null=True , blank=True)
    remarks = models.TextField(null=True, blank=True)
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='judged_scores' , null=True , blank=True
    )
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE , null=True , blank=True)
    updated_at = models.DateTimeField(auto_now=True , null=True , blank=True)
    is_bye = models.BooleanField(default=False)
    points_awarded = models.IntegerField(default=0 , null=True , blank=True)
    heat = models.ForeignKey(EventHeat, on_delete=models.CASCADE, null=True , blank=True)
    round_number = models.IntegerField(null=True , blank=True)
    position = models.IntegerField(null=True)  # Position in the heat
    time_taken = models.DurationField(null=True , blank=True)  # For time-based events
    qualified_for_next = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['sub_event', 'event_registration', 'stage', 'judge']
        ordering = ['sub_event', 'stage', '-total_score']

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
        # points = 2 if self.score_type == 'WINNER' else 1  # Example point values
        
        dept_score, created = DepartmentScore.objects.get_or_create(
            department=registration.department,
            year=registration.year,
            division=registration.division,
            sub_event=self.sub_event,
            defaults={
                    'total_score': self.total_score,
                    # 'points': points,
                    'updated_at': timezone.now()
                }
        )
        
        if not created:
            # dept_score.points = points
            dept_score.save()

class DepartmentScore(models.Model):
    department = models.CharField(max_length=50)
    year = models.CharField(max_length=10)
    division = models.CharField(max_length=10)
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    # points = models.IntegerField(default=0)
    total_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['department', 'year', 'division', 'sub_event']
        
    def __str__(self):
        return f"{self.department} {self.year} {self.division} - {self.sub_event.name}"
    
    