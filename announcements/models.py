from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Announcement(models.Model):
    PRIORITY_LEVELS = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent')
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    departments = models.CharField(max_length=200, null=True, blank=True)
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True)
    
    def __str__(self):
        return self.title