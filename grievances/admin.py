# grievances/admin.py
from django.contrib import admin
from .models import Grievance, MediaFile

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'submitted_by', 'status', 'submission_date')
    list_filter = ('status', 'grievance_type')
    search_fields = ('title', 'description')

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'file_type', 'uploaded_by', 'upload_date')
    list_filter = ('file_type', 'is_public')
    search_fields = ('description',)