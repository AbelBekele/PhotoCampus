from django.contrib import admin
from .models import Post, Comment, Like, Share

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'university', 'company', 'department', 'is_private', 'created_at')
    list_filter = ('created_at', 'author', 'university', 'company', 'department', 'is_private', 'event_date')
    search_fields = ('title', 'content', 'author__username', 'location', 'event_name')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Post Information', {
            'fields': ('title', 'content', 'image', 'author')
        }),
        ('Organization', {
            'fields': ('university', 'company', 'department', 'is_private')
        }),
        ('Event Details', {
            'fields': ('location', 'event_name', 'event_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

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