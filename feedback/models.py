from django.db import models
from django.utils.text import slugify
from users.models import User, CouncilMember


# Create your models here.
class FeedbackCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name

class Feedback(models.Model):
    FEEDBACK_STATUS = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected')
    )
    
    category = models.ForeignKey(FeedbackCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=FEEDBACK_STATUS, default='PENDING')
    is_anonymous = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='feedback/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.status}"

class FeedbackResponse(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='responses')
    response = models.TextField()
    responded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    response_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to {self.feedback.title}"