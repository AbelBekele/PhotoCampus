# PhotoCampus Feed System: Technical & Logical Deep Dive

The PhotoCampus feed is a personalized content delivery system designed specifically for university and corporate environments. Unlike typical social media feeds, it's tailored to show educational and professional content from organizations the user is affiliated with.

## Data Models & Relationships

### Core Models

1. **Post Model**
   - Central entity containing content (title, text, images)
   - Can be associated with either a University, Company, or be a personal post
   - Contains metadata like event details, location, and privacy settings
   - Has timestamps (created_at, updated_at)

2. **Interaction Models**
   - **Comments**: User-generated responses to posts
   - **Likes**: Simple engagement marker from users
   - **Shares**: Records when users share content to external platforms

3. **Organization Models**
   - **University**: Educational institutions with departments
   - **Company**: Corporate entities (like photography studios)
   - **Department**: Subdivisions within universities
   - **OrganizationMembership**: Tracks user affiliations with organizations

4. **Feed-Specific Models**
   - **FeedEntry**: Persists precomputed feed entries for users using fan-out-on-write pattern
   - **Follow**: Tracks user follow relationships that affect feed content
   - **CelebrityPostCache**: Special handling for high-follower users to prevent fan-out storms

## Feed Architecture (Hybrid Approach)

PhotoCampus uses a hybrid feed architecture that combines two standard patterns:

### 1. Fan-Out-On-Write (Push Model)
When a post is created, it's immediately distributed to the feeds of relevant users:

```python
@receiver(post_save, sender=Post)
def distribute_post_on_save(sender, instance, created, **kwargs):
    """When a post is created, trigger a Celery task to distribute it to feeds."""
    if created:
        from .tasks import distribute_post_to_feeds
        distribute_post_to_feeds.delay(instance.id)
```

### 2. Pull Model for Special Cases
For "celebrity" users (those with many followers), a pull-based approach is used:

```python
# For "celebrities," mark their posts for pull-based feed
if is_celebrity:
    CelebrityPostCache.objects.create(
        author_id=author.id,
        post_id=post_id
    )
    # Only distribute to a limited set
    active_followers = list(FeedEntry.objects.filter(
        user_id__in=recipient_users
    ).values('user_id').annotate(
        activity=Count('id')
    ).order_by('-activity')[:100].values_list('user_id', flat=True))
```

## Celery Task System

The feed system leverages Celery, a distributed task queue, to handle computationally intensive operations asynchronously:

### 1. Feed Distribution Tasks

```python
@shared_task
def distribute_post_to_feeds(post_id):
    """Fan-out on write: distribute a new post to followers' feeds."""
    # Identify recipients based on:
    # - Followers (for personal posts)
    # - Organization members (for org posts)
    # Process in batches to avoid memory issues
    for i in range(0, len(recipients_list), batch_size):
        batch = recipients_list[i:i+batch_size]
        _distribute_post_to_batch.delay(post_id, batch)
```

### 2. Feed Scoring & Personalization Tasks

```python
def calculate_post_score(post, user):
    """Calculate a personalized relevance score for a post and user."""
    # Score factors:
    # - Recency score (0-10 points, decays over 7 days)
    # - Engagement score (0-5 points) based on likes, comments, shares
    # - Organization relevance (0-5 points) for posts from user's orgs
    # - Small random factor to prevent exact ties
    return recency_score + engagement_score + org_relevance + random_factor
```

### 3. Periodic Maintenance Tasks

```python
@shared_task
def rebuild_inactive_feeds(days=7):
    """Periodic task to rebuild feeds for users who haven't been active in X days."""
    # Find users who haven't logged in for X days
    # Schedule feed refreshes for them in batches
```

```python
@shared_task
def cleanup_old_feeds(days=90):
    """Periodic task to clean up old feed entries."""
    management.call_command('cleanup_old_feeds', days=days)
```

### 4. Interaction-Triggered Tasks

```python
@shared_task
def update_feed_for_interaction(user_id, post_id, interaction_type):
    """Update feed scores when a user interacts with a post."""
    # Mark post as interacted in user's feed
    # Update cache entry if it exists
```

## Redis Integration

Redis powers several critical components of the feed system:

### 1. Celery Broker & Result Backend

```python
# Celery Configuration using Redis
CELERY_BROKER_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
```

### 2. Feed Caching

```python
# Cache feed entries for quick retrieval
cache_key = f"user:feed:{user.id}"
cache.set(cache_key, feed_entries_for_cache, timeout=settings.FEED_CACHE_TTL)
```

### 3. Connection Pooling & Performance Optimizations

```python
# Redis connection pool settings
CELERY_REDIS_SOCKET_TIMEOUT = 5
CELERY_REDIS_SOCKET_CONNECT_TIMEOUT = 5
CELERY_REDIS_MAX_CONNECTIONS = 20
```

## Feed Generation Algorithm

The feed algorithm (`home_feed` in API) works as follows:

### 1. Authentication & Filtering

```python
# Only authenticated users can access their feed
if not user.is_authenticated:
    return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
```

### 2. Content Selection Criteria

The feed only includes:
- Posts from the last 30 days (recency filter)
- Public posts OR posts from organizations the user is a member of

```python
base_query = Post.objects.filter(
    Q(is_private=False) | 
    Q(university__in=user.administered_universities.all()) |
    Q(university__in=[m.university for m in user.organization_memberships.all() if m.university]) |
    Q(company__in=[m.company for m in user.organization_memberships.all() if m.company])
).filter(
    created_at__gte=thirty_days_ago
)
```

### 3. Performance Optimization

Database queries are optimized to reduce load:
- `select_related` for foreign key relationships 
- `prefetch_related` for many-to-many relationships
- Result caching (with configurable TTL)

```python
.select_related('author', 'university', 'company', 'department')
.prefetch_related(
    Prefetch('comments', queryset=Comment.objects.select_related('author').order_by('-created_at')),
    'likes', 
    'shares'
)
```

### 4. Content Ranking Algorithm

Posts are ranked based on a sophisticated scoring system:

```python
posts_with_stats = base_query.annotate(
    # Basic engagement counting
    like_count=Count('likes', distinct=True),
    comment_count=Count('comments', distinct=True),
    share_count=Count('shares', distinct=True),
    
    # Weighted engagement score (comments and shares weighted higher)
    total_engagement=Count('likes', distinct=True) + 
                    Count('comments', distinct=True) * 2 + 
                    Count('shares', distinct=True) * 3,
    
    # Organization relevance boost
    org_relevance=Count(
        'university', 
        filter=Q(university__in=[m.university for m in user.organization_memberships.all()]) | 
              Q(company__in=[m.company for m in user.organization_memberships.all()]),
        distinct=True
    ) * 5
)
```

### 5. Algorithm Variants

The API supports different algorithm variations:
```python
# Apply algorithm sorting based on user preference
if algorithm == 'chronological':
    posts_with_stats = posts_with_stats.order_by('-created_at')
elif algorithm == 'engagement':
    posts_with_stats = posts_with_stats.order_by('-total_engagement', '-created_at')
else:  # 'mixed' - default
    posts_with_stats = posts_with_stats.order_by('-created_at', '-total_engagement', '-org_relevance')
```

## Scaling & Performance Features

### 1. Batched Processing
Large operations are broken into batches to prevent memory issues:
```python
# Process users in batches
batch_size = 100
for i in range(0, len(inactive_users), batch_size):
    batch = inactive_users[i:i+batch_size]
    for user_id in batch:
        refresh_feed_for_user.delay(user_id)
```

### 2. Celebrity User Handling
Special logic for high-follower "celebrity" users prevents fan-out storms:
```python
# For users with many followers, use a different distribution approach
if len(recipient_users) > 1000:
    # Store in CelebrityPostCache instead of fanning out to all followers
    # Only distribute to most active followers
```

### 3. Rate Limiting & Throttling
API endpoints use throttling to prevent abuse:
```python
class PostRateThrottle(throttling.UserRateThrottle):
    rate = '20/day'
    scope = 'post_create'

class LikeRateThrottle(throttling.UserRateThrottle):
    rate = '200/day'
    scope = 'like'
```

## Frontend Implementation

1. **Pagination**: Implemented with page parameters for efficient loading
   ```javascript
   function fetchHomeFeed(page = 1) {
       const url = `/api/posts/home_feed/?page=${page}&page_size=10`;
       // ...
   }
   ```

2. **Dynamic Rendering**: Content is rendered using a template system
   ```javascript
   function renderPosts(posts, append = false) {
       const feedContainer = document.getElementById('feed-content');
       const postTemplate = document.getElementById('post-template');
       // ...
   }
   ```

3. **Empty States**: The system handles cases where no content is available
   ```javascript
   if (data.length === 0) {
       // Display empty feed suggestions
   }
   ```

4. **Load More Functionality**: Additional content is loaded on demand
   ```javascript
   document.getElementById('load-more-btn').addEventListener('click', () => {
       currentPage++;
       fetchHomeFeed(currentPage);
   });
   ```

## Technical Implementation Details

### API Endpoints

- **REST API**: `/api/posts/home_feed/` (with pagination parameters)
- **GraphQL**: `homeFeed` query (with limit and offset parameters)

### Caching Strategy

The system implements caching to improve performance:
```python
# Try to get from cache first (only for first page)
cache_key = f'home_feed_{user.id}_page{page}_size{page_size}'
cached_data = cache.get(cache_key)
if cached_data:
    return Response(cached_data)
```

Cache invalidation occurs when:
- New posts are created
- Posts are interacted with (likes, comments, shares)

### Security Considerations

1. **Privacy Filtering**: Private posts are only visible to organization members
2. **Authentication Required**: Only logged-in users can access the feed
3. **Organization-Based Access Control**: Content visibility respects organization boundaries

## What Makes PhotoCampus Feed Different

Unlike general social media platforms:

1. **Organization-Centric**: Content is primarily organized around educational institutions and companies
2. **Hybrid Architecture**: Combines push and pull models for optimal performance
3. **Asynchronous Processing**: Uses Celery for heavy operations without affecting user experience
4. **Enhanced Caching**: Multi-level cache strategy with Redis and database persistence
5. **Algorithmic Flexibility**: Supports multiple feed algorithms that users can choose from
6. **Efficient Scaling**: Special handling for high-follower accounts and large batch operations
7. **Scheduled Maintenance**: Automatic cleanup and feed refreshes keep the system healthy

This architecture makes PhotoCampus particularly suited for institutional photo sharing compared to general social media platforms, where the focus is on individual connections rather than organizational affiliations.
