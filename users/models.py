# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import slugify
from django.db import models

class User(AbstractUser):
    USER_TYPES = (
        ('ADMIN', 'Admin'),
        ('COUNCIL', 'Student Council'),
        ('STUDENT', 'Student'),
        ('FACULTY', 'Faculty')
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    department = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.SlugField(null=True, blank=True)
    email = models.EmailField(unique=True)  # Make email required and unique
    id_card_document = models.FileField(
        upload_to='id_cards/',
        null=True,
        blank=True,
        help_text="Required for Students and Council members"
    )
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_valid_until = models.DateTimeField(null=True, blank=True)
    division = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    roll_number = models.CharField(max_length=20, null=True, blank=True)
    year_of_study = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.username

class CouncilMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    term_start = models.DateField()
    term_end = models.DateField()
    responsibilities = models.TextField()
    achievements = models.SlugField(null=True, blank=True)
    linkedin_profile = models.URLField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.position}"

class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    designation = models.CharField(max_length=100)
    subjects = models.CharField(max_length=200)
    office_location = models.CharField(max_length=100, null=True, blank=True)
    office_hours = models.CharField(max_length=100, null=True, blank=True)
    research_interests = models.SlugField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.designation}"
    
    class Meta:
        db_table = 'users'
