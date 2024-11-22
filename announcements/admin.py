# announcements/admin.py
from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'created_by', 'created_at', 'expiry_date')
    list_filter = ('priority', 'created_at')
    search_fields = ('title', 'content')