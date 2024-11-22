from django.urls import path
from . import views

urlpatterns = [
    path('', views.resource_list, name='resource-list'),
    path('categories/', views.category_list, name='resource-categories'),
    path('create/', views.create_resource, name='create-resource'),
    path('categories/create/', views.create_category, name='create-category'),
    path('categories/<slug:slug>/', views.category_detail, name='category-detail'),
    path('<slug:slug>/', views.resource_detail, name='resource-detail'),
    path('<slug:slug>/download/', views.download_resource, name='download-resource'),
    path('<slug:slug>/update/', views.update_resource, name='update-resource'),
]