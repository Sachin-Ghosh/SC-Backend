# grievances/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from users.models import User, CouncilMember
from events.models import Event,SubEvent

class Grievance(models.Model):
    GRIEVANCE_TYPES = (
        ('CHEATING', 'Cheating'),
        ('MISCONDUCT', 'Misconduct'),
        ('RULES_VIOLATION', 'Rules Violation'),
        ('OTHER', 'Other')
    )
    
    GRIEVANCE_STATUS = (
        ('PENDING', 'Pending'),
        ('INVESTIGATING', 'Under Investigation'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected')
    )
    
    event = models.ForeignKey(SubEvent, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    grievance_type = models.CharField(max_length=20, choices=GRIEVANCE_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    evidence = models.ManyToManyField('MediaFile', blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=GRIEVANCE_STATUS, default='PENDING')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_grievances')
    resolution = models.TextField(null=True, blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)

class MediaFile(models.Model):
    FILE_TYPES = (
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document'),
        ('AUDIO', 'Audio')
    )
    
    file = models.FileField(upload_to='media/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    size = models.IntegerField()  # File size in bytes
    is_public = models.BooleanField(default=True)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='grievance_media_files'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grievance_media_files'
    )