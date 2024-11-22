# gallery/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('albums/', views.album_list, name='album-list'),
    path('albums/create/', views.create_album, name='create-album'),
    path('albums/<slug:slug>/', views.album_detail, name='album-detail'),
    path('albums/<slug:slug>/upload/', views.upload_media, name='upload-media'),
]