from django.contrib import admin
from .models import Post, Comment, Like, Share, Follow

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

class LikeInline(admin.TabularInline):
    model = Like
    extra = 0

class ShareInline(admin.TabularInline):
    model = Share
    extra = 0

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'university', 'company', 'is_private')
    list_filter = ('is_private', 'university', 'company', 'created_at')
    search_fields = ('title', 'content', 'author__username', 'location', 'event_name')
    date_hierarchy = 'created_at'
    inlines = [CommentInline, LikeInline, ShareInline]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'post__title')
    date_hierarchy = 'created_at'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')
    date_hierarchy = 'created_at'

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'shared_with', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title', 'shared_with')
    date_hierarchy = 'created_at'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followed', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'followed__username')
    date_hierarchy = 'created_at'

# Temporarily removed until FeedEntry model is properly implemented
# @admin.register(FeedEntry)
# class FeedEntryAdmin(admin.ModelAdmin):
#     list_display = ('user', 'post', 'score', 'viewed', 'interacted', 'created_at')
#     list_filter = ('viewed', 'interacted', 'created_at')
#     search_fields = ('user__username', 'post__title')
#     date_hierarchy = 'created_at'
#     readonly_fields = ('score',)