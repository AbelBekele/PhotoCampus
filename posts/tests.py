from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from organizations.models import University, OrganizationMembership
from .models import Post, Comment, Like, Share
from datetime import timedelta
from django.utils import timezone

class HomeFeedTests(TestCase):
    """Test suite for the home feed functionality"""
    
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.user3 = User.objects.create_user(username='user3', password='password123')
        
        # Create organizations
        self.university = University.objects.create(
            name='Test University',
            description='A test university'
        )
        
        # Add user1 to university
        self.membership = OrganizationMembership.objects.create(
            university=self.university,
            user=self.user1,
            role='Student'
        )
        
        # Create posts
        # Public post by user2
        self.public_post = Post.objects.create(
            title='Public Post',
            content='This is a public post',
            author=self.user2,
            is_private=False
        )
        
        # University post (private)
        self.uni_post = Post.objects.create(
            title='University Post',
            content='This is a university post',
            author=self.user3,
            university=self.university,
            is_private=True
        )
        
        # Old post (shouldn't appear in feed)
        old_date = timezone.now() - timedelta(days=60)
        self.old_post = Post.objects.create(
            title='Old Post',
            content='This is an old post',
            author=self.user2,
            is_private=False
        )
        self.old_post.created_at = old_date
        self.old_post.save()
        
        # Post with engagement
        self.engagement_post = Post.objects.create(
            title='Engagement Post',
            content='This post has likes and comments',
            author=self.user3,
            is_private=False
        )
        
        # Add engagement
        Like.objects.create(post=self.engagement_post, user=self.user1)
        Comment.objects.create(
            post=self.engagement_post,
            author=self.user1,
            content='Great post!'
        )
        
        # API client
        self.client = APIClient()
    
    def test_home_feed_unauthenticated(self):
        """Test that unauthenticated users can't access the home feed"""
        url = reverse('post-home-feed')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_home_feed_authenticated(self):
        """Test that authenticated users can access their home feed"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('post-home-feed')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # We should get at least 3 posts (public_post, uni_post, engagement_post)
        self.assertGreaterEqual(len(response.data), 3)
        
        # The old post should not be in the feed
        post_ids = [post['id'] for post in response.data]
        self.assertNotIn(self.old_post.id, post_ids)
        
        # Engagement post should be prioritized (first in the list)
        self.assertEqual(response.data[0]['id'], self.engagement_post.id)
        
        # Both public and private (university) posts should be accessible
        uni_post_ids = [post['id'] for post in response.data if post['university'] is not None]
        self.assertIn(self.uni_post.id, uni_post_ids)
    
    def test_graphql_home_feed(self):
        """Test the GraphQL home feed query"""
        # This would need to use the GraphQL client
        # We'll implement this later
        pass
