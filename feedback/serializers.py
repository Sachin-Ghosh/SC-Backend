# feedback/serializers.py
from rest_framework import serializers
from .models import FeedbackCategory, Feedback, FeedbackResponse

class FeedbackCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackCategory
        fields = '__all__'

class FeedbackResponseSerializer(serializers.ModelSerializer):
    responded_by_name = serializers.CharField(source='responded_by.username', read_only=True)
    
    class Meta:
        model = FeedbackResponse
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    responses = FeedbackResponseSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Feedback
        fields = '__all__'