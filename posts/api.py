from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Comment, Like, Share
from .serializers import PostSerializer, CommentSerializer, LikeSerializer, ShareSerializer
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'university', 'company', 'department', 'is_private']
    search_fields = ['title', 'content', 'location', 'event_name']
    ordering_fields = ['created_at', 'updated_at', 'title']
    
    def perform_create(self, serializer):
        """When a new post is created, invalidate any home feed caches"""
        result = serializer.save(author=self.request.user)
        
        # Invalidate cache for all users
        # In a real-world scenario, you might want to be more selective
        # about which caches to invalidate
        cache_keys = cache.keys('home_feed_*')
        if cache_keys:
            cache.delete_many(cache_keys)
            
        return result
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        Like.objects.get_or_create(post=post, user=request.user)
        return Response({'status': 'post liked'})
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        post = self.get_object()
        Like.objects.filter(post=post, user=request.user).delete()
        return Response({'status': 'post unliked'})
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        post = self.get_object()
        shared_with = request.data.get('shared_with', '')
        Share.objects.create(post=post, user=request.user, shared_with=shared_with)
        return Response({'status': 'post shared'})

    @action(detail=False, methods=['get'])
    def home_feed(self, request):
        """
        Returns a personalized home feed based on:
        1. User's organization memberships
        2. Post engagement (likes, comments, shares)
        3. Content recency
        """
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
            
        # Get params
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        # Try to get from cache first (only for first page)
        cache_key = f'home_feed_{user.id}_page{page}_size{page_size}'
        cached_data = None
        
        if page == 1:
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)
        
        # Get recent posts (last 30 days)
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
        
        # Posts the user has interacted with
        user_interacted_posts = Post.objects.filter(
            Q(likes__user=user) | 
            Q(comments__author=user) | 
            Q(shares__user=user)
        ).distinct()
        
        # Calculate engagement score and add organization relevance
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
        
        # Paginate results
        start = (page - 1) * page_size
        end = page * page_size
        
        # Give interacted posts higher priority by boosting them to the top
        # but limit to 5 so they don't overwhelm the feed
        interacted_posts = posts_with_stats.filter(id__in=user_interacted_posts.values_list('id', flat=True))[:5]
        
        # Regular posts make up the rest of the feed
        remaining_count = min(page_size - len(interacted_posts), posts_with_stats.count())
        regular_posts = posts_with_stats.exclude(id__in=interacted_posts.values_list('id', flat=True))[:remaining_count]
        
        # Combine results
        combined_posts = list(interacted_posts) + list(regular_posts)
        
        # Serialize
        serializer = PostSerializer(combined_posts, many=True, context={'request': request})
        serialized_data = serializer.data
        
        # Cache the result for 10 minutes (only for first page)
        if page == 1:
            cache.set(cache_key, serialized_data, 60 * 10)  # 10 minutes
        
        return Response(serialized_data)

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'author']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class LikeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows likes to be viewed.
    """
    queryset = Like.objects.all().order_by('-created_at')
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'user']

class ShareViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows shares to be viewed.
    """
    queryset = Share.objects.all().order_by('-created_at')
    serializer_class = ShareSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'user'] 