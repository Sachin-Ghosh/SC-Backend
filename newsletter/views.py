from django.shortcuts import render

# Create your views here.
# newsletter/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Newsletter, Subscriber
from .serializers import NewsletterSerializer, SubscriberSerializer

class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        newsletter = self.get_object()
        newsletter.is_published = True
        newsletter.published_date = datetime.now()
        newsletter.save()
        return Response({'status': 'newsletter published'})

class SubscriberViewSet(viewsets.ModelViewSet):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        subscriber = self.get_object()
        subscriber.is_active = False
        subscriber.save()
        return Response({'status': 'unsubscribed successfully'})