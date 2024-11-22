# achievements/models.py
from django.db import models
from django.utils.text import slugify
from users.models import User, CouncilMember

# resources/models.py
class ResourceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    RESOURCE_TYPES = (
        ('DOCUMENT', 'Document'),
        ('VIDEO', 'Video'),
        ('LINK', 'External Link'),
        ('TEMPLATE', 'Template')
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ResourceCategory, on_delete=models.CASCADE)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    description = models.TextField()
    file = models.FileField(upload_to='resources/', null=True, blank=True)
    external_link = models.URLField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)
    download_count = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title