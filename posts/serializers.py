from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post, Comment, Like, Share
from django.conf import settings
import os

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        ref_name = "PostsUserSerializer"

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
    likes = LikeSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    shares_count = serializers.SerializerMethodField()
    image = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'image', 'image_url', 
                  'author', 'university', 'company', 'department', 'is_private', 'location', 
                  'event_name', 'event_date', 'created_at', 'updated_at', 'comments', 
                  'likes', 'likes_count', 'shares_count']
        read_only_fields = ['created_at', 'updated_at', 'author']
    
    def get_image_url(self, obj):
        """
        Return the absolute URL for the image if it exists.
        The frontend will handle resizing with CSS or other client-side techniques.
        """
        if not obj.image:
            return None
        
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def validate_image(self, value):
        if value:
            # Check file size (limit to 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image size cannot exceed 5MB")
            
            # Check file type
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not a valid image")
                
        return value
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_shares_count(self, obj):
        return obj.shares.count()
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Ensure image URL is absolute
        if representation.get('image') and not representation['image'].startswith('http'):
            request = self.context.get('request')
            if request:
                representation['image'] = request.build_absolute_uri(representation['image'])
        
        return representation 