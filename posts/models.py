from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Post(models.Model):
    """Model representing a user post."""
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    
    # Organization association - can be null for personal posts
    university = models.ForeignKey('organizations.University', on_delete=models.CASCADE, 
                                 related_name='posts', null=True, blank=True)
    company = models.ForeignKey('organizations.Company', on_delete=models.CASCADE, 
                              related_name='posts', null=True, blank=True)
    # For university posts, can be associated with a department
    department = models.ForeignKey('organizations.Department', on_delete=models.SET_NULL, 
                                 related_name='posts', null=True, blank=True)
    
    # Is this post public or private to the organization?
    is_private = models.BooleanField(default=False, 
                                   help_text="If private, only organization members can view")
    
    # Photo collection metadata
    location = models.CharField(max_length=255, blank=True, 
                              help_text="Where the photo was taken")
    event_name = models.CharField(max_length=255, blank=True,
                                help_text="Name of the event if applicable")
    event_date = models.DateField(null=True, blank=True,
                                help_text="Date when the event occurred")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
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
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']

class Like(models.Model):
    """Model representing a like on a post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('post', 'user')
        
    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"

class Share(models.Model):
    """Model representing a share of a post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.CharField(max_length=255, blank=True, null=True, help_text="Platform or person the post was shared with")
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} shared {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
