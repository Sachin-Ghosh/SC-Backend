# newsletter/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.newsletter_list, name='newsletter-list'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('unsubscribe/', views.unsubscribe, name='unsubscribe'),
    path('create/', views.create_newsletter, name='create-newsletter'),
    path('<int:pk>/', views.newsletter_detail, name='newsletter-detail'),
]