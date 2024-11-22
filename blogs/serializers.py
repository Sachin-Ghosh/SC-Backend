# blogs/serializers.py
from rest_framework import serializers
from .models import BlogCategory, BlogPost, Comment

class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'author', 'author_name', 'content', 'created_at']

class BlogPostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = BlogPost
        fields = '__all__'