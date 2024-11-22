# resources/admin.py
from django.contrib import admin
from .models import ResourceCategory, Resource

@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'resource_type', 'uploaded_by', 'is_public')
    list_filter = ('resource_type', 'is_public', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}