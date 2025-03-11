from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class Post(models.Model):
    """Model representing a user post."""
    title = models.CharField(max_length=255, validators=[MinLengthValidator(3)], 
                          help_text="Title of the post (3-255 characters)",
                          db_index=True)
    content = models.TextField(validators=[MinLengthValidator(10)],
                             help_text="Content of the post (min 10 characters)")
    image = models.ImageField(upload_to='posts/', blank=True, null=True,
                            help_text="Image for the post (optional)")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts',
                             db_index=True)
    
    # Organization association - can be null for personal posts
    university = models.ForeignKey('organizations.University', on_delete=models.CASCADE, 
                                 related_name='posts', null=True, blank=True,
                                 db_index=True)
    company = models.ForeignKey('organizations.Company', on_delete=models.CASCADE, 
                              related_name='posts', null=True, blank=True,
                              db_index=True)
    # For university posts, can be associated with a department
    department = models.ForeignKey('organizations.Department', on_delete=models.SET_NULL, 
                                 related_name='posts', null=True, blank=True,
                                 db_index=True)
    
    # Is this post public or private to the organization?
    is_private = models.BooleanField(default=False, 
                                   help_text="If private, only organization members can view",
                                   db_index=True)
    
    # Photo collection metadata
    location = models.CharField(max_length=255, blank=True, 
                              help_text="Where the photo was taken",
                              db_index=True)
    event_name = models.CharField(max_length=255, blank=True,
                                help_text="Name of the event if applicable",
                                db_index=True)
    event_date = models.DateField(null=True, blank=True,
                                help_text="Date when the event occurred",
                                db_index=True)
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at', 'author']),
            models.Index(fields=['is_private', 'university']),
            models.Index(fields=['is_private', 'company']),
            models.Index(fields=['location', 'event_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    # Either personal post (both null) or organization post (exactly one not null)
                    (models.Q(university__isnull=True) & models.Q(company__isnull=True)) |
                    (
                        (models.Q(university__isnull=False) & models.Q(company__isnull=True)) |
                        (models.Q(university__isnull=True) & models.Q(company__isnull=False))
                    )
                ),
                name='post_must_have_zero_or_one_organization'
            )
        ]

class Comment(models.Model):
    """Model representing a comment on a post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments',
                          db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments',
                            db_index=True)
    content = models.TextField(validators=[MinLengthValidator(3)],
                            help_text="Comment content (min 3 characters)")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['post', 'author']),
        ]

class Like(models.Model):
    """Model representing a like on a post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes',
                          db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes',
                          db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        unique_together = ('post', 'user')
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
        
    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"

class Share(models.Model):
    """Model representing a share of a post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares',
                          db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares',
                          db_index=True)
    shared_with = models.CharField(max_length=255, blank=True, null=True, 
                                help_text="Platform or person the post was shared with")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    def __str__(self):
        return f"{self.user.username} shared {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

class Follow(models.Model):
    """Model representing a follow relationship between users."""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following',
                              db_index=True)
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers',
                              db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        unique_together = ('follower', 'followed')
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['followed', 'created_at']),
        ]
        
    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"

class FeedEntry(models.Model):
    """Model representing a feed entry for a user.
    
    This model is used for persisting feed entries that are precomputed
    for users through the fan-out-on-write pattern.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_entries',
                           db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='feed_appearances',
                          db_index=True)
    score = models.FloatField(default=0.0, 
                           help_text="Relevance score for ranking", 
                           db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Has the user viewed this entry?
    viewed = models.BooleanField(default=False)
    # Has the user interacted with this post?
    interacted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Feed entry for {self.user.username}: {self.post.title}"
    
    class Meta:
        ordering = ['-score', '-created_at']
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['user', 'score']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'viewed']),
            models.Index(fields=['user', 'interacted']),
        ]

class CelebrityPostCache(models.Model):
    """
    Model to store celebrity post data that was previously stored in Redis.
    This replaces the Redis-based storage with a database-backed solution.
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='celebrity_posts')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='celebrity_cache')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('author', 'post')
        indexes = [
            models.Index(fields=['author']),
            models.Index(fields=['post']),
            models.Index(fields=['created_at']),
        ]

@receiver(post_save, sender=Post)
def distribute_post_on_save(sender, instance, created, **kwargs):
    """
    When a post is created, trigger a Celery task to distribute it to feeds.
    Uses the fan-out-on-write pattern.
    """
    # Temporarily disabled until Redis and Celery are configured
    pass
    # if created:
    #     # Import here to avoid circular imports
    #     from .tasks import distribute_post_to_feeds
    #     distribute_post_to_feeds.delay(instance.id)
