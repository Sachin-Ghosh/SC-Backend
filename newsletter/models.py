from django.db import models
from django.utils.text import slugify
from users.models import User, CouncilMember

# Create your models here.
class Newsletter(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    published_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to='newsletters/', null=True, blank=True)
    
    def __str__(self):
        return self.title

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.email