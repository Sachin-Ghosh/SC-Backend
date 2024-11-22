from django.db import models
from django.utils.text import slugify
from users.models import User, CouncilMember

class Achievement(models.Model):
    ACHIEVEMENT_TYPES = (
        ('ACADEMIC', 'Academic'),
        ('SPORTS', 'Sports'),
        ('CULTURAL', 'Cultural'),
        ('RESEARCH', 'Research'),
        ('INNOVATION', 'Innovation'),
        ('SOCIAL', 'Social Work')
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    description = models.TextField()
    achiever = models.ForeignKey(User, on_delete=models.CASCADE)
    date_achieved = models.DateField()
    proof_document = models.FileField(upload_to='achievements/', null=True, blank=True)
    certificate = models.FileField(upload_to='achievements/certificates/', null=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='verified_achievements')
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.achiever.username} - {self.title}"
    
    class Meta:
        app_label = 'achievements'  # Add this inner class