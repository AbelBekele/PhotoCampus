import json
import logging
from django.contrib.auth.models import User
from django.db.models import Q, Count, F, Prefetch, Sum, Exists, OuterRef
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from celery import shared_task
from django.core.cache import cache

from .models import Post, Comment, Like, Share, Follow, FeedEntry, CelebrityPostCache
from organizations.models import OrganizationMembership

logger = logging.getLogger(__name__)

# Helper functions for feed distribution
def calculate_post_score(post, user):
    """
    Calculate a personalized relevance score for a post and user.
    Higher score means higher relevance.
    
    Factors:
    - Recency (newer posts score higher)
    - Organization relevance (posts from user's orgs score higher)
    - Content preference (based on user's interaction history)
    - Engagement (posts with more interactions score higher)
    """
    now = timezone.now()
    
    # Base score: recency (0-10 points, decays over 7 days)
    time_diff = max(0, min(7, (now - post.created_at).days))
    recency_score = 10 * (1 - time_diff / 7)
    
    # Engagement score (0-5 points)
    likes_count = post.likes.count()
    comments_count = post.comments.count() 
    shares_count = post.shares.count()
    
    engagement_score = min(5, (likes_count + (2 * comments_count) + (3 * shares_count)) / 10)
    
    # Organization relevance (0-5 points)
    org_relevance = 0
    user_orgs = set()
    
    # Get user's organizations
    for membership in user.organization_memberships.all():
        if membership.university:
            user_orgs.add(('university', membership.university.id))
        if membership.company:
            user_orgs.add(('company', membership.company.id))
    
    # Check post organization against user's organizations
    if post.university and ('university', post.university.id) in user_orgs:
        org_relevance += 5
    elif post.company and ('company', post.company.id) in user_orgs:
        org_relevance += 5
    
    # Calculate final score (max 20 points)
    final_score = recency_score + engagement_score + org_relevance
    
    # Add small random factor (0-0.5) to prevent exact ties
    import random
    final_score += random.random() * 0.5
    
    return final_score

@shared_task
def distribute_post_to_feeds(post_id):
    """
    Fan-out on write: distribute a new post to followers' feeds.
    
    For users with many followers, this task can be heavy, so it's
    run asynchronously via Celery.
    """
    try:
        post = Post.objects.select_related('author', 'university', 'company').get(id=post_id)
        author = post.author
        
        # Strategy: 
        # 1. For personal posts: distribute to followers
        # 2. For org posts: distribute to organization members
        recipient_users = set()
        
        # If personal post or public profile, send to followers
        if not post.company and not post.university:
            # Get author's followers
            follower_ids = list(Follow.objects.filter(
                followed=author
            ).values_list('follower_id', flat=True))
            
            for follower_id in follower_ids:
                recipient_users.add(follower_id)
        
        # If org post, distribute to org members
        if post.university:
            members = OrganizationMembership.objects.filter(
                university=post.university
            ).values_list('user_id', flat=True)
            
            for member_id in members:
                recipient_users.add(member_id)
        
        if post.company:
            members = OrganizationMembership.objects.filter(
                company=post.company
            ).values_list('user_id', flat=True)
            
            for member_id in members:
                recipient_users.add(member_id)
        
        # Add the author themselves
        recipient_users.add(author.id)
        
        # If this is a highly-followed user (e.g., a "celebrity" with many followers)
        # we might want to use a special handling to avoid fan-out storms
        is_celebrity = len(recipient_users) > 1000
        
        # For "celebrities," mark their followers for pull-based feed
        # instead of pushing to all followers
        if is_celebrity:
            # Use database instead of Redis
            # Create a CelebrityPostCache entry
            CelebrityPostCache.objects.create(
                author_id=author.id,
                post_id=post_id
            )
            
            # Only distribute to a limited set (e.g., most active followers)
            active_followers = list(FeedEntry.objects.filter(
                user_id__in=recipient_users
            ).values('user_id').annotate(
                activity=Count('id')
            ).order_by('-activity')[:100].values_list('user_id', flat=True))
            
            recipient_users = set(active_followers)
        
        # Now distribute to all recipients
        batch_size = 500
        recipients_list = list(recipient_users)
        
        for i in range(0, len(recipients_list), batch_size):
            batch = recipients_list[i:i+batch_size]
            _distribute_post_to_batch.delay(post_id, batch)
        
        return f"Post {post_id} distributed to {len(recipient_users)} feeds"
    
    except Post.DoesNotExist:
        logger.error(f"Post {post_id} does not exist")
        return f"Error: Post {post_id} not found"
    except Exception as e:
        logger.error(f"Error distributing post {post_id}: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def _distribute_post_to_batch(post_id, user_ids):
    """Process a batch of users for post distribution"""
    try:
        post = Post.objects.get(id=post_id)
        users = User.objects.filter(id__in=user_ids)
        
        # Distribute to SQL for persistence
        feed_entries = []
        for user in users:
            score = calculate_post_score(post, user)
            feed_entries.append(FeedEntry(
                user=user,
                post=post,
                score=score,
                # Mark as interacted if it's the user's own post or they've already interacted
                interacted=(user.id == post.author.id)
            ))
        
        # Bulk create feed entries in DB
        FeedEntry.objects.bulk_create(feed_entries, ignore_conflicts=True)
        
        # Use Django's cache framework instead of direct Redis access
        for user in users:
            score = next((fe.score for fe in feed_entries if fe.user_id == user.id), 0)
            cache_key = f"user:feed:{user.id}"
            
            feed_entry = {
                "post_id": post.id,
                "score": score,
                "created_at": post.created_at.isoformat(),
                "author_id": post.author_id,
                "title": post.title,
                "content_preview": post.content[:100] if post.content else "",
            }
            
            # Get existing feed from cache
            user_feed = cache.get(cache_key, [])
            
            # Add new entry
            user_feed.append(feed_entry)
            
            # Sort by score
            user_feed = sorted(user_feed, key=lambda x: x["score"], reverse=True)
            
            # Limit to 100 entries
            user_feed = user_feed[:100]
            
            # Store back in cache
            cache.set(cache_key, user_feed, timeout=settings.FEED_CACHE_TTL)
        
        return f"Batch of {len(user_ids)} feeds updated with post {post_id}"
    
    except Exception as e:
        logger.error(f"Error in batch distribution for post {post_id}: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def refresh_feed_for_user(user_id):
    """
    Rebuild a user's feed completely.
    Useful for new users or when preferences change significantly.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # First, clean up old feed entries
        FeedEntry.objects.filter(user=user).delete()
        
        # Get user's organization memberships
        user_universities = OrganizationMembership.objects.filter(
            user=user, university__isnull=False
        ).values_list('university_id', flat=True)
        
        user_companies = OrganizationMembership.objects.filter(
            user=user, company__isnull=False
        ).values_list('company_id', flat=True)
        
        # Get user's followed users
        followed_users = Follow.objects.filter(
            follower=user
        ).values_list('followed_id', flat=True)
        
        # Build a query for relevant posts
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        posts = Post.objects.filter(
            # Content filter - posts user has permissions to see
            Q(is_private=False) | 
            Q(author=user) |
            Q(author_id__in=followed_users) |
            Q(university_id__in=user_universities) |
            Q(company_id__in=user_companies),
            # Time filter - only recent posts
            created_at__gte=thirty_days_ago
        ).select_related(
            'author', 'university', 'company'
        ).distinct()
        
        # Create feed entries for each post
        feed_entries = []
        redis_entries = {}
        
        for post in posts:
            score = calculate_post_score(post, user)
            
            # Check if user has interacted with this post
            interacted = Like.objects.filter(post=post, user=user).exists() or \
                        Comment.objects.filter(post=post, author=user).exists() or \
                        Share.objects.filter(post=post, user=user).exists() or \
                        post.author == user
            
            feed_entries.append(FeedEntry(
                user=user,
                post=post,
                score=score,
                interacted=interacted
            ))
            
            # Prepare Redis entry
            redis_entries[json.dumps({
                "post_id": post.id,
                "author_id": post.author.id,
                "created_at": post.created_at.timestamp(),
                "score": score
            })] = score
        
        # Bulk create feed entries in DB
        FeedEntry.objects.bulk_create(feed_entries, ignore_conflicts=True)
        
        # Update cache instead of Redis
        cache_key = f"user:feed:{user.id}"
        
        # Clear existing feed from cache
        cache.delete(cache_key)
        
        # Create new feed entries for cache
        feed_entries_for_cache = []
        for entry in feed_entries:
            post = entry.post
            feed_entry = {
                "post_id": post.id,
                "score": entry.score,
                "created_at": post.created_at.isoformat(),
                "author_id": post.author_id,
                "title": post.title,
                "content_preview": post.content[:100] if post.content else "",
            }
            feed_entries_for_cache.append(feed_entry)
        
        # Sort by score
        feed_entries_for_cache = sorted(feed_entries_for_cache, key=lambda x: x["score"], reverse=True)
        
        # Store in cache
        cache.set(cache_key, feed_entries_for_cache, timeout=settings.FEED_CACHE_TTL)
        
        return f"Feed refreshed for user {user.username} with {len(feed_entries)} entries"
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} does not exist")
        return f"Error: User {user_id} not found"
    except Exception as e:
        logger.error(f"Error refreshing feed for user {user_id}: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def update_feed_for_interaction(user_id, post_id, interaction_type):
    """
    Update feed scores when a user interacts with a post.
    
    Interaction types: 'like', 'comment', 'share', 'view'
    
    This accomplishes two things:
    1. Marks the specific post as interacted in the user's feed
    2. Updates the user's content preferences for future ranking
    """
    try:
        # Mark post as interacted in user's feed
        if interaction_type != 'view':
            FeedEntry.objects.filter(user_id=user_id, post_id=post_id).update(
                interacted=True
            )
        else:
            FeedEntry.objects.filter(user_id=user_id, post_id=post_id).update(
                viewed=True
            )
        
        # Update cache entry if it exists
        cache_key = f"user:feed:{user_id}"
        
        # Get all entries for this user's feed from cache
        user_feed = cache.get(cache_key, [])
        
        # Update the viewed status for the specific post
        for entry in user_feed:
            if entry["post_id"] == post_id:
                entry["viewed"] = True
                break
        
        # Store back in cache
        cache.set(cache_key, user_feed, timeout=settings.FEED_CACHE_TTL)
        
        return f"Feed updated for interaction: User {user_id}, Post {post_id}, Type {interaction_type}"
    except Exception as e:
        logger.error(f"Error updating feed for interaction: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def rebuild_inactive_feeds(days=7):
    """
    Periodic task to rebuild feeds for users who haven't been active in X days.
    This ensures feeds stay fresh even for less active users.
    
    Args:
        days: Number of days of inactivity to trigger rebuild
    """
    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timedelta
    
    # Users who haven't been active for the specified number of days
    cutoff_date = timezone.now() - timedelta(days=days)
    
    inactive_users = User.objects.filter(
        last_login__lt=cutoff_date
    ).values_list('id', flat=True)
    
    logger.info(f"Rebuilding feeds for {len(inactive_users)} inactive users")
    
    # Process users in batches
    batch_size = 100
    for i in range(0, len(inactive_users), batch_size):
        batch = inactive_users[i:i+batch_size]
        for user_id in batch:
            refresh_feed_for_user.delay(user_id)
    
    return f"Scheduled feed rebuild for {len(inactive_users)} inactive users"

@shared_task
def cleanup_old_feeds(days=90):
    """
    Periodic task to clean up old feed entries.
    
    Args:
        days: Remove entries older than this many days
    """
    from django.core import management
    
    # Run the cleanup management command
    management.call_command('cleanup_old_feeds', days=days)
    
    return f"Cleaned up feed entries older than {days} days"