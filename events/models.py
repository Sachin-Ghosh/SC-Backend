# events/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import User
from users.models import CouncilMember

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
    created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='created_events'
)
    created_at = models.DateTimeField(auto_now_add=True)
    cover_image = models.ImageField(upload_to='events/')
    banner_image = models.ImageField(upload_to='events/banners/')
    rules_document = models.FileField(upload_to='events/rules/', null=True)
    schedule_file = models.FileField(upload_to='events/schedules/', null=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
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
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sub_events')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=EVENT_CATEGORIES)
    schedule = models.DateTimeField()
    venue = models.CharField(max_length=200)
    max_participants = models.IntegerField()
    registration_deadline = models.DateTimeField()
    coordinators = models.ManyToManyField(
    settings.AUTH_USER_MODEL,
    related_name='coordinated_subevents'
)
    registration_fee = models.DecimalField(max_digits=8, decimal_places=2)
    rules = models.TextField()
    scoring_criteria = models.TextField()
    prize_pool = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.event.name} - {self.name}"

class EventRegistration(models.Model):
    REGISTRATION_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    )
    
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    participant = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='event_registrations'
)
    team_name = models.CharField(max_length=100, null=True, blank=True)
    college_name = models.CharField(max_length=200, null=True, blank=True)
    department = models.CharField(max_length=100)
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='PENDING')
    payment_status = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    def __str__(self):
        return f"{self.participant.username} - {self.sub_event.name}"


class EventScore(models.Model):
    sub_event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    participant = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='received_scores'
)
    department = models.CharField(max_length=100)
    score = models.DecimalField(max_digits=8, decimal_places=2)
    remarks = models.TextField(null=True, blank=True)
    judge = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='judged_scores'
)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)