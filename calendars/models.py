from django.db import models
from django.utils.text import slugify
from users.models import User, CouncilMember

# Create your models here.
class CalendarEvent(models.Model):
    EVENT_TYPES = (
        ('ACADEMIC', 'Academic'),
        ('CULTURAL', 'Cultural'),
        ('SPORTS', 'Sports'),
        ('MEETING', 'Meeting'),
        ('OTHER', 'Other')
    )
    
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, null=True, blank=True)
    reminder_enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class EventAttendee(models.Model):
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE)
    attendee = models.ForeignKey(User, on_delete=models.CASCADE)
    response_status = models.CharField(max_length=20, choices=[
        ('YES', 'Attending'),
        ('NO', 'Not Attending'),
        ('MAYBE', 'Maybe'),
        ('PENDING', 'Pending')
    ])
    
    class Meta:
        unique_together = ('event', 'attendee')
    
    def __str__(self):
        return f"{self.attendee.username} - {self.event.title}"