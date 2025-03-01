from django.contrib import admin
from .models import Post, Comment, Like, Share

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('title', 'content', 'author__username')
    date_hierarchy = 'created_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username', 'post__title')
    date_hierarchy = 'created_at'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('post__title', 'user__username')
    date_hierarchy = 'created_at'

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'shared_with', 'created_at')
    list_filter = ('created_at', 'user', 'shared_with')
    search_fields = ('post__title', 'user__username', 'shared_with')
    date_hierarchy = 'created_at'