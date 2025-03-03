import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth.models import User
from .models import Post, Comment, Like, Share
from django.contrib.auth import get_user_model
from graphene import relay
import django_filters
from django.db.models import Q, Count, F, ExpressionWrapper, DateTimeField
from django.utils import timezone
from datetime import timedelta

# Define Types
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'posts', 'comments', 'likes', 'shares')
        filter_fields = {
            'username': ['exact', 'icontains'],
            'email': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class PostFilter(django_filters.FilterSet):
    title_contains = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    content_contains = django_filters.CharFilter(field_name='content', lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    author_username = django_filters.CharFilter(field_name='author__username', lookup_expr='exact')
    search = django_filters.CharFilter(method='filter_search')
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) | 
            Q(content__icontains=value) |
            Q(author__username__icontains=value) |
            Q(location__icontains=value) |
            Q(event_name__icontains=value)
        )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'author', 'created_at']

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = '__all__'
        filterset_class = PostFilter
        interfaces = (graphene.relay.Node,)

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = '__all__'
        filter_fields = {
            'content': ['icontains'],
            'author__username': ['exact'],
            'post__id': ['exact'],
            'created_at': ['exact', 'gt', 'lt'],
        }
        interfaces = (graphene.relay.Node,)

class LikeType(DjangoObjectType):
    class Meta:
        model = Like
        fields = '__all__'
        filter_fields = {
            'user__username': ['exact'],
            'post__id': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class ShareType(DjangoObjectType):
    class Meta:
        model = Share
        fields = '__all__'
        filter_fields = {
            'user__username': ['exact'],
            'post__id': ['exact'],
            'shared_with': ['exact', 'icontains'],
            'created_at': ['exact', 'gt', 'lt'],
        }
        interfaces = (graphene.relay.Node,)

# Query
class Query(graphene.ObjectType):
    # User queries
    me = graphene.Field(UserType)
    user = graphene.relay.Node.Field(UserType)
    all_users = DjangoFilterConnectionField(UserType)
    
    # Single item queries
    post = graphene.relay.Node.Field(PostType)
    comment = graphene.relay.Node.Field(CommentType)
    like = graphene.relay.Node.Field(LikeType)
    share = graphene.relay.Node.Field(ShareType)
    
    # List queries
    all_posts = DjangoFilterConnectionField(PostType)
    all_comments = DjangoFilterConnectionField(CommentType)
    all_likes = DjangoFilterConnectionField(LikeType)
    all_shares = DjangoFilterConnectionField(ShareType)
    
    # Search posts
    search_posts = graphene.List(
        PostType, 
        search_term=graphene.String(required=True),
        limit=graphene.Int(default_value=10)
    )
    
    # Get posts with comments and likes count (optimized query)
    posts_with_stats = graphene.List(
        PostType,
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )
    
    # Home Feed query - personalized content without follows
    home_feed = graphene.List(
        PostType,
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0)
    )
    
    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
    def resolve_all_users(self, info, **kwargs):
        return User.objects.all()
    
    def resolve_all_posts(self, info, **kwargs):
        # Optimize with select_related for foreign keys
        return Post.objects.select_related('author', 'university', 'company', 'department').all()
    
    def resolve_all_comments(self, info, **kwargs):
        # Optimize with select_related
        return Comment.objects.select_related('author', 'post').all()
    
    def resolve_all_likes(self, info, **kwargs):
        # Optimize with select_related
        return Like.objects.select_related('user', 'post').all()
    
    def resolve_all_shares(self, info, **kwargs):
        # Optimize with select_related
        return Share.objects.select_related('user', 'post').all()
    
    def resolve_search_posts(self, info, search_term, limit):
        if not search_term:
            return Post.objects.none()
            
        filter = (
            Q(title__icontains=search_term) | 
            Q(content__icontains=search_term) |
            Q(author__username__icontains=search_term) |
            Q(location__icontains=search_term) |
            Q(event_name__icontains=search_term)
        )
        
        # Optimize with select_related
        return Post.objects.select_related('author').filter(filter)[:limit]
    
    def resolve_posts_with_stats(self, info, limit, offset):
        # Highly optimized query for posts with stats
        return Post.objects.select_related('author', 'university', 'company', 'department')\
                .prefetch_related('comments', 'likes', 'shares')\
                .order_by('-created_at')[offset:offset+limit]
    
    def resolve_home_feed(self, info, limit=20, offset=0):
        user = info.context.user
        if not user.is_authenticated:
            return Post.objects.none()
            
        # Calculate a date 30 days ago for recent content
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Base queryset - only public posts or posts from user's organizations
        base_query = Post.objects.filter(
            Q(is_private=False) | 
            Q(university__in=user.administered_universities.all()) |
            Q(university__in=[m.university for m in user.organization_memberships.all() if m.university]) |
            Q(company__in=[m.company for m in user.organization_memberships.all() if m.company])
        ).filter(
            created_at__gte=thirty_days_ago
        ).select_related(
            'author', 'university', 'company', 'department'
        ).prefetch_related(
            'likes', 'comments', 'shares'
        ).distinct()
        
        # Posts the user has interacted with (liked, commented, shared)
        user_interacted_posts = Post.objects.filter(
            Q(likes__user=user) | 
            Q(comments__author=user) | 
            Q(shares__user=user)
        ).distinct()
        
        # Calculate engagement score - more likes, comments, shares = higher score
        # Also prioritize recent content
        posts_with_stats = base_query.annotate(
            like_count=Count('likes', distinct=True),
            comment_count=Count('comments', distinct=True),
            share_count=Count('shares', distinct=True),
            total_engagement=Count('likes', distinct=True) + Count('comments', distinct=True) * 2 + Count('shares', distinct=True) * 3,
            # Posts from user's organizations get a boost
            org_relevance=Count(
                'university', 
                filter=Q(
                    university__in=[m.university for m in user.organization_memberships.all() if m.university]
                ) | Q(
                    company__in=[m.company for m in user.organization_memberships.all() if m.company]
                ),
                distinct=True
            ) * 5
        ).order_by('-created_at', '-total_engagement', '-org_relevance')
        
        # Give interacted posts higher priority by boosting them to the top
        # but limit to 5 so they don't overwhelm the feed
        interacted_posts = posts_with_stats.filter(id__in=user_interacted_posts.values_list('id', flat=True))[:5]
        
        # Regular posts make up the rest of the feed
        regular_posts = posts_with_stats.exclude(id__in=interacted_posts.values_list('id', flat=True))[:(limit-interacted_posts.count())]
        
        # Combine the two sets
        return list(interacted_posts) + list(regular_posts)

# User Registration
class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)

    user = graphene.Field(UserType)

    def mutate(self, info, username, email, password, first_name=None, last_name=None):
        User = get_user_model()
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            raise Exception('Username already exists')
        if User.objects.filter(email=email).exists():
            raise Exception('Email already exists')
        
        # Create new user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name or '',
            last_name=last_name or ''
        )
        
        return CreateUser(user=user)

# Update CreatePost mutation
class CreatePost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        # Note: Image upload is not directly supported in GraphQL
        # We would need to implement a separate endpoint for that

    post = graphene.Field(PostType)

    def mutate(self, info, title, content):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to create a post!')
        
        post = Post(
            title=title,
            content=content,
            author=user
        )
        post.save()
        
        return CreatePost(post=post)

# Mutations
class CreateComment(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    comment = graphene.Field(CommentType)

    def mutate(self, info, post_id, content):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to comment!')
        
        post = Post.objects.get(pk=post_id)
        comment = Comment(
            post=post,
            author=user,
            content=content
        )
        comment.save()
        
        return CreateComment(comment=comment)

class LikePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)

    like = graphene.Field(LikeType)
    
    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to like a post!')
        
        post = Post.objects.get(pk=post_id)
        
        # Check if user already liked the post
        like, created = Like.objects.get_or_create(
            post=post,
            user=user
        )
        
        if not created:
            # User already liked this post
            raise Exception('You have already liked this post!')
        
        return LikePost(like=like)

class UnlikePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to unlike a post!')
        
        try:
            like = Like.objects.get(post_id=post_id, user=user)
            like.delete()
            return UnlikePost(success=True)
        except Like.DoesNotExist:
            return UnlikePost(success=False)

class SharePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)
        shared_with = graphene.String(required=False)

    share = graphene.Field(ShareType)
    
    def mutate(self, info, post_id, shared_with=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to share a post!')
        
        post = Post.objects.get(pk=post_id)
        
        share = Share(
            post=post,
            user=user,
            shared_with=shared_with
        )
        share.save()
        
        return SharePost(share=share)

class UpdatePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)
        title = graphene.String()
        content = graphene.String()
        is_private = graphene.Boolean()
        location = graphene.String()
        event_name = graphene.String()
        event_date = graphene.Date()

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, post_id, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to update a post!')
            
        try:
            post = Post.objects.get(pk=post_id)
            
            # Check if user is the author
            if post.author != user:
                raise Exception('You can only update your own posts!')
                
            # Update fields if provided
            for key, value in kwargs.items():
                if value is not None:
                    setattr(post, key, value)
            
            post.save()
            return UpdatePost(post=post, success=True, message="Post updated successfully")
            
        except Post.DoesNotExist:
            return UpdatePost(success=False, message="Post not found")

class DeletePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to delete a post!')
            
        try:
            post = Post.objects.get(pk=post_id)
            
            # Check if user is the author
            if post.author != user:
                raise Exception('You can only delete your own posts!')
                
            # Delete the post
            post.delete()
            return DeletePost(success=True, message="Post deleted successfully")
            
        except Post.DoesNotExist:
            return DeletePost(success=False, message="Post not found")

class DeleteComment(graphene.Mutation):
    class Arguments:
        comment_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, comment_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to delete a comment!')
            
        try:
            comment = Comment.objects.get(pk=comment_id)
            
            # Check if user is the author or the post author
            if comment.author != user and comment.post.author != user:
                raise Exception('You can only delete your own comments or comments on your posts!')
                
            # Delete the comment
            comment.delete()
            return DeleteComment(success=True, message="Comment deleted successfully")
            
        except Comment.DoesNotExist:
            return DeleteComment(success=False, message="Comment not found")

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_post = CreatePost.Field()
    create_comment = CreateComment.Field()
    like_post = LikePost.Field()
    unlike_post = UnlikePost.Field()
    share_post = SharePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    delete_comment = DeleteComment.Field() 