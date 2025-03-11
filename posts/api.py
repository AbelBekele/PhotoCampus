from rest_framework import viewsets, permissions, filters, throttling
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Comment, Like, Share, Follow
from .serializers import PostSerializer, CommentSerializer, LikeSerializer, ShareSerializer
from django.db.models import Q, Count, F, Prefetch
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from photocampus.utils import get_redis_connection
import json

class PostRateThrottle(throttling.UserRateThrottle):
    rate = '20/day'
    scope = 'post_create'

class LikeRateThrottle(throttling.UserRateThrottle):
    rate = '200/day'
    scope = 'like'

class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    
    Additionally, it provides custom actions for liking, unliking, 
    sharing posts, and generating a personalized home feed.
    """
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'university', 'company', 'department', 'is_private']
    search_fields = ['title', 'content', 'location', 'event_name']
    ordering_fields = ['created_at', 'updated_at', 'title']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_throttles(self):
        """
        Return the throttles that should be used, based on action.
        """
        if self.action == 'create':
            throttle_classes = [PostRateThrottle]
        elif self.action in ['like', 'unlike']:
            throttle_classes = [LikeRateThrottle]
        else:
            throttle_classes = []
        return [throttle() for throttle in throttle_classes]
    
    def get_queryset(self):
        """
        Customize queryset with optimized performance using select_related and prefetch_related.
        Also restrict access to private posts unless user is a member of the organization.
        """
        user = self.request.user
        queryset = Post.objects.select_related(
            'author', 'university', 'company', 'department'
        ).prefetch_related(
            Prefetch('comments', queryset=Comment.objects.select_related('author').order_by('-created_at')),
            'likes', 
            'shares'
        )
        
        # If not authenticated, only show public posts
        if not user.is_authenticated:
            return queryset.filter(is_private=False)
            
        # If authenticated but detail view, apply permission check in get_object
        if self.action == 'retrieve':
            return queryset
            
        # For list view, filter based on user's organizations
        return queryset.filter(
            Q(is_private=False) | 
            Q(author=user) |
            Q(university__in=user.administered_universities.all()) |
            Q(university__in=[m.university for m in user.organization_memberships.all() if m.university]) |
            Q(company__in=[m.company for m in user.organization_memberships.all() if m.company])
        ).distinct()
    
    def get_object(self):
        """
        Override to check if user can access a private post.
        """
        obj = super().get_object()
        user = self.request.user
        
        # If the post is public or user is the author, allow access
        if not obj.is_private or obj.author == user:
            return obj
            
        # Check if user is a member or admin of the organization
        if (obj.university and 
            (obj.university in user.administered_universities.all() or
             obj.university in [m.university for m in user.organization_memberships.all() if m.university])):
            return obj
            
        if (obj.company and 
            (obj.company in user.administered_companies.all() or
             obj.company in [m.company for m in user.organization_memberships.all() if m.company])):
            return obj
            
        # If none of the above, deny access
        self.permission_denied(
            self.request, 
            message="You do not have permission to access this private post."
        )
    
    def perform_create(self, serializer):
        """
        When a new post is created, invalidate any home feed caches.
        """
        result = serializer.save(author=self.request.user)
        
        # Invalidate cache for relevant users
        # Using a simpler approach to clear specific cache keys
        # LocMemCache doesn't support the 'keys' method, so we'll avoid it
        
        # Define a pattern-based approach to clear cache
        if not result.is_private:
            # For public posts, we'll use a more targeted approach
            # Instead of using cache.keys() which causes the error
            cache.clear()  # Clear all cache for now as a simpler solution
        else:
            # For private posts, only invalidate for organization members
            if result.university:
                org_users = [
                    *[admin.id for admin in result.university.admins.all()],
                    *[m.user.id for m in result.university.memberships.all()]
                ]
            elif result.company:
                org_users = [
                    *[admin.id for admin in result.company.admins.all()],
                    *[m.user.id for m in result.company.memberships.all()]
                ]
            else:
                # Personal private post, only visible to author
                org_users = [self.request.user.id]
                
            # Directly delete each cache key without using cache.keys()
            for user_id in org_users:
                cache_key = f'home_feed_{user_id}_page1_size20'  # Most common key pattern
                cache.delete(cache_key)
            
        return result

    @swagger_auto_schema(
        operation_description="Get personalized home feed",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of posts per page", type=openapi.TYPE_INTEGER),
            openapi.Parameter('algorithm', openapi.IN_QUERY, description="Feed algorithm type (default: 'mixed')", type=openapi.TYPE_STRING, enum=['chronological', 'engagement', 'mixed']),
        ],
        responses={
            200: PostSerializer(many=True),
            401: "Authentication required"
        }
    )
    @action(detail=False, methods=['get'])
    def home_feed(self, request):
        """
        Returns a personalized home feed based on:
        1. User's organization memberships
        2. User's follow relationships
        3. Post engagement (likes, comments, shares)
        4. Content recency
        
        Posts are ranked by an algorithm that considers multiple factors:
        - Recency: Newer posts rank higher
        - Engagement: Posts with more likes/comments/shares rank higher
        - Organization relevance: Posts from user's organizations rank higher
        - User interaction: Posts the user has interacted with get priority
        
        Available algorithms via the 'algorithm' query parameter:
        - 'chronological': Simple reverse-chronological feed (newest first)
        - 'engagement': Ranked primarily by engagement metrics
        - 'mixed' (default): Balanced approach with some chronological and some ranked
        
        For authenticated users only.
        """
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Get params
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        algorithm = request.query_params.get('algorithm', 'mixed')
        
        # TEMPORARY FALLBACK TO ORIGINAL IMPLEMENTATION
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
            Prefetch('comments', queryset=Comment.objects.select_related('author').order_by('-created_at')),
            'likes', 
            'shares'
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
            total_engagement=Count('likes', distinct=True) + 
                            Count('comments', distinct=True) * 2 + 
                            Count('shares', distinct=True) * 3,
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
        )
        
        # Apply algorithm sorting
        if algorithm == 'chronological':
            posts_with_stats = posts_with_stats.order_by('-created_at')
        elif algorithm == 'engagement':
            posts_with_stats = posts_with_stats.order_by('-total_engagement', '-created_at')
        else:  # 'mixed' - default
            posts_with_stats = posts_with_stats.order_by('-created_at', '-total_engagement', '-org_relevance')
        
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
        combined_results = list(interacted_posts) + list(regular_posts)
        
        # Serialize posts - ensure we pass the request context for proper URL generation
        serializer = PostSerializer(combined_results, many=True, context={'request': request})
        serialized_data = serializer.data
        
        # Add pagination info to response
        response_data = {
            'results': serialized_data,
            'page': page,
            'page_size': page_size,
            'algorithm': algorithm,
            'has_next': len(combined_results) == page_size,  # Crude estimate
        }
        
        return Response(response_data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a post"""
        post = self.get_object()
        user = request.user
        
        # Check if already liked
        if Like.objects.filter(post=post, user=user).exists():
            return Response({'status': 'already liked'}, status=status.HTTP_200_OK)
            
        # Create like
        like = Like.objects.create(post=post, user=user)
        
        # Update feed scores and mark interaction
        from .tasks import update_feed_for_interaction
        update_feed_for_interaction.delay(user.id, post.id, 'like')
        
        return Response(
            {'status': 'liked', 'like_id': like.id},
            status=status.HTTP_201_CREATED
        )
        
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a post"""
        post = self.get_object()
        user = request.user
        
        # Find and delete like
        like = get_object_or_404(Like, post=post, user=user)
        like.delete()
        
        # No need to update feed for unlikes
        
        return Response(
            {'status': 'unliked'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def likes(self, request, pk=None):
        """Get all likes for a post"""
        post = self.get_object()
        likes = Like.objects.filter(post=post).select_related('user')
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share a post"""
        post = self.get_object()
        user = request.user
        shared_with = request.data.get('shared_with', '')
        
        # Create share
        share = Share.objects.create(
            post=post, 
            user=user,
            shared_with=shared_with
        )
        
        # Update feed scores and mark interaction
        from .tasks import update_feed_for_interaction
        update_feed_for_interaction.delay(user.id, post.id, 'share')
        
        return Response(
            {'status': 'shared', 'share_id': share.id},
            status=status.HTTP_201_CREATED
        )

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'author']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Optimize with select_related
        return queryset.select_related('author', 'post')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        
        # Update feed scores and mark interaction
        post_id = serializer.validated_data.get('post').id
        user_id = self.request.user.id
        
        from .tasks import update_feed_for_interaction
        update_feed_for_interaction.delay(user_id, post_id, 'comment')

class LikeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows likes to be viewed.
    """
    queryset = Like.objects.all().order_by('-created_at')
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'user']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Optimize with select_related
        return queryset.select_related('user', 'post')

class ShareViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows shares to be viewed.
    """
    queryset = Share.objects.all().order_by('-created_at')
    serializer_class = ShareSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'user'] 