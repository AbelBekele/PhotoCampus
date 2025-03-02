from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post, Comment, Like, Share

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'created_at']
        read_only_fields = ['created_at']

class ShareSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Share
        fields = ['id', 'post', 'user', 'shared_with', 'created_at']
        read_only_fields = ['created_at']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    shares_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'image', 'author', 'university', 'company', 
                  'department', 'is_private', 'location', 'event_name', 'event_date', 
                  'created_at', 'updated_at', 'comments', 'likes_count', 'shares_count']
        read_only_fields = ['created_at', 'updated_at', 'author']
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_shares_count(self, obj):
        return obj.shares.count() 