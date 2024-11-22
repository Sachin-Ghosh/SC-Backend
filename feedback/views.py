from django.shortcuts import render

# Create your views here.
# feedback/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FeedbackCategory, Feedback, FeedbackResponse
from .serializers import (FeedbackCategorySerializer, FeedbackSerializer, 
                        FeedbackResponseSerializer)

class FeedbackCategoryViewSet(viewsets.ModelViewSet):
    queryset = FeedbackCategory.objects.all()
    serializer_class = FeedbackCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def add_response(self, request, pk=None):
        feedback = self.get_object()
        serializer = FeedbackResponseSerializer(data={
            'feedback': feedback.id,
            'responded_by': request.user.id,
            'response': request.data.get('response')
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)