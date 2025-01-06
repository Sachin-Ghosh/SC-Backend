
# Register your models here.
# users/admin.py
from django.contrib import admin
from .models import User, CouncilMember, Faculty

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'department', 'year_of_study', 'get_full_name')
    list_filter = ('user_type', 'department', 'year_of_study')
    search_fields = ('username', 'email', 'roll_number',  'first_name', 'last_name')
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email
    get_full_name.short_description = 'Full Name'

@admin.register(CouncilMember)
class CouncilMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'term_start', 'term_end')
    list_filter = ('position', 'term_start', 'term_end')
    search_fields = ('user__username', 'position')

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('user', 'designation', 'subjects')
    list_filter = ('designation',)
    search_fields = ('user__username', 'subjects')