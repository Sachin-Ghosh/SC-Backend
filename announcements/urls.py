# announcements/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.announcement_list, name='announcement-list'),
    path('create/', views.create_announcement, name='create-announcement'),
    path('<int:pk>/', views.announcement_detail, name='announcement-detail'),
    path('<int:pk>/update/', views.update_announcement, name='update-announcement'),
]