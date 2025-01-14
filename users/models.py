# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import slugify
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

class User(AbstractUser):
    GENDER_CHOICES = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other')
    )
    USER_TYPES = (
        ('ADMIN', 'Admin'),
        ('COUNCIL', 'Student Council'),
        ('STUDENT', 'Student'),
        ('FACULTY', 'Faculty')
    )
    DEPARTMENT_TYPES = (
        ('AS&H','AS&H'),
        ('COMPUTER', 'Comps'),
        ('IT', 'IT'),
        ('AIML', 'AIML'),
        ('DE', 'DE'),
        ('CIVIL', 'Civil'),
        ('OTHER', 'Other')
    )
    DIVISION_TYPES = (
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
        ('F', 'F')
    )
    YEAR_TYPES = (
        ('FE', 'FE'),
        ('SE', 'SE'),
        ('TE', 'TE'),
        ('BE', 'BE')
    )
    
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES,
        null=True , blank=True,
        default='OTHER'  # Setting 'Other' as default for existing records
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    department = models.CharField(max_length=100, choices=DEPARTMENT_TYPES)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True)
    id_card_document = models.ImageField(
        upload_to='id_cards/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        help_text="Required for Students and Council members. Image files only (jpg, jpeg, png)"
    )
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_valid_until = models.DateTimeField(null=True, blank=True)
    division = models.TextField(null=True, blank=True, choices=DIVISION_TYPES)
    phone = models.CharField(max_length=15,null=True, blank=True)
    roll_number = models.CharField(max_length=20, null=True, blank=True)
    year_of_study = models.TextField(null=True, blank=True, choices=YEAR_TYPES)
    reset_password_token = models.CharField(max_length=100, null=True, blank=True)
    reset_password_token_valid_until = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.username

    def clean(self):
        # Validate college email except for FE students
        if self.year_of_study != 'FE' and not self.email.endswith('@universal.edu.in'):  # Replace with your college domain
            raise ValidationError('Must use college email address')
        
        # Validate ID card requirement
        if self.user_type in ['STUDENT', 'COUNCIL'] and not self.id_card_document:
            raise ValidationError('ID card document is required for students and council members')
    def get_full_name(self):
        """Return the full name of the user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    def save(self, *args, **kwargs):
        # Auto increment year in June
        if self.year_of_study:
            current_month = timezone.now().month
            if current_month == 6:  # June
                year_mapping = {'FE': 'SE', 'SE': 'TE', 'TE': 'BE'}
                if self.year_of_study in year_mapping:
                    self.year_of_study = year_mapping[self.year_of_study]
        
        super().save(*args, **kwargs)

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
    subjects = models.CharField(max_length=200, null=True, blank=True)
    office_location = models.CharField(max_length=100, null=True, blank=True)
    office_hours = models.CharField(max_length=100, null=True, blank=True)
    research_interests = models.SlugField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.designation}"
    
    class Meta:
        db_table = 'users'
