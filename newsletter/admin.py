# newsletter/admin.py
from django.contrib import admin
from .models import Newsletter, Subscriber

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'subscribed_at', 'is_active')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email', 'name')