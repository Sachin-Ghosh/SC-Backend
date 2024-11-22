# feedback/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.feedback_list, name='feedback-list'),
    path('categories/', views.category_list, name='feedback-categories'),
    path('submit/', views.submit_feedback, name='submit-feedback'),
    path('<int:pk>/', views.feedback_detail, name='feedback-detail'),
    path('<int:pk>/respond/', views.respond_to_feedback, name='respond-to-feedback'),
]