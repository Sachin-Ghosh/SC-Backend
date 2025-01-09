# grievances/serializers.py
from rest_framework import serializers
from .models import Grievance, MediaFile

class MediaFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFile
        fields = [
            'id', 'file', 'file_url', 'file_type', 'description',
            'uploaded_by', 'uploaded_by_name', 'upload_date',
            'size', 'is_public', 'event'
        ]
        read_only_fields = ['uploaded_by', 'size', 'upload_date']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None
    
    def get_uploaded_by_name(self, obj):
        return str(obj.uploaded_by) if obj.uploaded_by else None

class GrievanceSerializer(serializers.ModelSerializer):
    evidence = MediaFileSerializer(many=True, read_only=True)
    submitted_by_name = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Grievance
        fields = [
            'id', 'event', 'event_name', 'submitted_by', 'submitted_by_name',
            'grievance_type', 'title', 'description', 'evidence',
            'submission_date', 'status', 'assigned_to', 'assigned_to_name',
            'resolution', 'resolved_date'
        ]
        read_only_fields = ['submitted_by', 'submission_date', 'resolved_date']
    
    def get_submitted_by_name(self, obj):
        return str(obj.submitted_by) if obj.submitted_by else None
    
    def get_event_name(self, obj):
        return str(obj.event) if obj.event else None
    
    def get_assigned_to_name(self, obj):
        return str(obj.assigned_to) if obj.assigned_to else None