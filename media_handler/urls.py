# media_handler/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_media, name='upload-media'),
    path('files/', views.media_list, name='media-list'),
    path('files/<int:pk>/', views.media_detail, name='media-detail'),
    path('files/<int:pk>/delete/', views.delete_media, name='delete-media'),
]