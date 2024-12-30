# media_handler/models.py
from django.db import models
from django.conf import settings
from events.models import Event
from grievances.models import Grievance

class MediaFile(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    grievance = models.ForeignKey(Grievance, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='media/')
    upload_date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='event_media_files'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_media_files' , null=True 
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    media_type = models.CharField(max_length=50)  # e.g., 'image', 'video', 'document'
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.title