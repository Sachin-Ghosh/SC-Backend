from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.BlogCategoryViewSet, basename='category')
router.register(r'posts', views.BlogPostViewSet, basename='post')

urlpatterns = [
    # Blog Post URLs
    path('', views.blog_list, name='blog-list'),
    path('create/', views.create_post, name='create-post'),
    path('<slug:slug>/', views.blog_detail, name='blog-detail'),
    path('<slug:slug>/update/', views.update_post, name='update-post'),
    path('<slug:slug>/delete/', views.delete_post, name='delete-post'),
    path('<slug:slug>/publish/', views.publish_post, name='publish-post'),
    path('<slug:slug>/unpublish/', views.unpublish_post, name='unpublish-post'),
    
    # Category URLs
    path('categories/', views.category_list, name='category-list'),
    path('categories/create/', views.create_category, name='create-category'),
    path('categories/<slug:slug>/', views.category_detail, name='category-detail'),
    path('categories/<slug:slug>/update/', views.update_category, name='update-category'),
    path('categories/<slug:slug>/delete/', views.delete_category, name='delete-category'),
    
    # Comment URLs
    path('<slug:slug>/comments/', views.post_comments, name='post-comments'),
    path('<slug:slug>/comments/add/', views.add_comment, name='add-comment'),
    path('comments/<int:pk>/update/', views.update_comment, name='update-comment'),
    path('comments/<int:pk>/delete/', views.delete_comment, name='delete-comment'),
    
    # Filter and Search URLs
    path('by-category/<slug:category_slug>/', views.posts_by_category, name='posts-by-category'),
    path('by-author/<int:author_id>/', views.posts_by_author, name='posts-by-author'),
    path('search/', views.search_posts, name='search-posts'),
    
    # Statistics and Analytics
    path('<slug:slug>/increment-views/', views.increment_views, name='increment-views'),
    path('popular/', views.popular_posts, name='popular-posts'),
    path('recent/', views.recent_posts, name='recent-posts'),
]

urlpatterns += router.urls