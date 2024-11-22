from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.template.defaultfilters import slugify
from events.models import Event


# Create your models here.
class Album(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='created_albums'
)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class Media(models.Model):
    MEDIA_TYPES = (
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document')
    )
    
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='media')
    title = models.CharField(max_length=200)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='gallery/')
    uploaded_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='uploaded_gallery_media'
)
    upload_date = models.DateTimeField(auto_now_add=True)
    caption = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.media_type}"