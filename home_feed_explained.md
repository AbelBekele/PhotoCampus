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

## Feed Generation Algorithm

The feed algorithm (`resolve_home_feed` in both REST API and GraphQL implementations) works as follows:

### 1. Authentication & Filtering

```python
# Only authenticated users can access their feed
if not user.is_authenticated:
    return Post.objects.none()
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
- Result caching (with 10-minute invalidation)

```python
# Optimized queries
.select_related('author', 'university', 'company', 'department')
.prefetch_related('likes', 'comments', 'shares')
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
    
    # Organization relevance boost (+5 points for posts from user's orgs)
    org_relevance=Count(
        'university', 
        filter=Q(university__in=[m.university for m in user.organization_memberships.all()]) | 
              Q(company__in=[m.company for m in user.organization_memberships.all()]),
        distinct=True
    ) * 5
).order_by('-created_at', '-total_engagement', '-org_relevance')
```

### 5. Personalization Factors

The feed prioritizes two types of content:

1. **User-Interacted Content**: Posts the user has liked, commented on, or shared get priority placement (limited to 5 posts to avoid overwhelming the feed)
   ```python
   # Posts the user has interacted with
   user_interacted_posts = Post.objects.filter(
       Q(likes__user=user) | 
       Q(comments__author=user) | 
       Q(shares__user=user)
   ).distinct()
   
   # Prioritize these posts (limited to top 5)
   interacted_posts = posts_with_stats.filter(
       id__in=user_interacted_posts.values_list('id', flat=True)
   )[:5]
   ```

2. **Organizationally Relevant Content**: Posts from the user's universities and companies get a scoring boost

### 6. Feed Composition

The final feed combines:
- Top user-interacted posts
- Other posts ranked by engagement and relevance

```python
# Combine the sets for the final feed
return list(interacted_posts) + list(regular_posts)
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
2. **No Follow System**: Content relevance is based on organizational membership, not following relationships
3. **Event-Focused**: Optimized for displaying event-based photo content (graduations, corporate events)
4. **Privacy-Aware**: Respects organizational boundaries for private content
5. **Engagement Weighted**: Comments and shares are weighted higher than likes in the ranking algorithm

This architecture makes PhotoCampus particularly suited for institutional photo sharing compared to general social media platforms, where the focus is on individual connections rather than organizational affiliations.
