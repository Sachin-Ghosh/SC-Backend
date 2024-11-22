from django.shortcuts import render

# Create your views here.
# blogs/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BlogCategory, BlogPost, Comment
from .serializers import BlogCategorySerializer, BlogPostSerializer, CommentSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

class BlogCategoryViewSet(viewsets.ModelViewSet):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'views_count']

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentSerializer(data={
            'post': post.id,
            'author': request.user.id,
            'content': request.data.get('content')
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        post = self.get_object()
        post.views_count += 1
        post.save()
        return Response({'views_count': post.views_count})
    

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    serializer = BlogPostSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    serializer = BlogPostSerializer(post)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.user != post.author and not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = BlogPostSerializer(post, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.user != post.author and not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.user != post.author and not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    post.is_published = True
    post.save()
    return Response({'status': 'published'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unpublish_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.user != post.author and not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    post.is_published = False
    post.save()
    return Response({'status': 'unpublished'})

# Category views
@api_view(['GET'])
def category_list(request):
    categories = BlogCategory.objects.all()
    serializer = BlogCategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_category(request):
    if not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = BlogCategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Comment views
@api_view(['GET'])
def post_comments(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    comments = Comment.objects.filter(post=post)
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_comment(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    serializer = CommentSerializer(data={
        'post': post.id,
        'author': request.user.id,
        'content': request.data.get('content')
    })
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Filter and Search views
@api_view(['GET'])
def posts_by_category(request, category_slug):
    posts = BlogPost.objects.filter(
        category__slug=category_slug,
        is_published=True
    ).order_by('-created_at')
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def search_posts(request):
    query = request.query_params.get('q', '')
    posts = BlogPost.objects.filter(
        Q(title__icontains=query) | 
        Q(content__icontains=query),
        is_published=True
    ).order_by('-created_at')
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)

# Statistics views
@api_view(['GET'])
def popular_posts(request):
    posts = BlogPost.objects.filter(
        is_published=True
    ).order_by('-views_count')[:10]
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def recent_posts(request):
    posts = BlogPost.objects.filter(
        is_published=True
    ).order_by('-created_at')[:10]
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)
# Add these category-related views to your existing views.py file

@api_view(['GET'])
def category_detail(request, slug):
    category = get_object_or_404(BlogCategory, slug=slug)
    serializer = BlogCategorySerializer(category)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_category(request, slug):
    if not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    category = get_object_or_404(BlogCategory, slug=slug)
    serializer = BlogCategorySerializer(category, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category(request, slug):
    if not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    category = get_object_or_404(BlogCategory, slug=slug)
    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    # Only allow comment author or staff to update
    if request.user != comment.author and not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CommentSerializer(comment, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    # Only allow comment author or staff to delete
    if request.user != comment.author and not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def posts_by_author(request, author_id):
    posts = BlogPost.objects.filter(
        author_id=author_id,
        is_published=True
    ).order_by('-created_at')
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def increment_views(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    post.views_count += 1
    post.save()
    return Response({'views_count': post.views_count})