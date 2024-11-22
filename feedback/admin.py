# feedback/admin.py
from django.contrib import admin
from .models import FeedbackCategory, Feedback, FeedbackResponse

@admin.register(FeedbackCategory)
class FeedbackCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'submitted_by', 'status', 'submission_date')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description')

@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ('feedback', 'responded_by', 'response_date')
    list_filter = ('response_date',)
    search_fields = ('response',)