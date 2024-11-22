# achievements/admin.py
from django.contrib import admin
from .models import Achievement

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'achiever', 'achievement_type', 'date_achieved', 'is_verified')
    list_filter = ('achievement_type', 'is_verified')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}