# gallery/admin.py
from django.contrib import admin
from .models import Album, Media

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('title', 'album', 'media_type', 'uploaded_by', 'upload_date')
    list_filter = ('media_type', 'upload_date')
    search_fields = ('title', 'caption')