from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from posts.models import Post, Comment, Like, Share
from organizations.models import University, Company, Department, OrganizationMembership
import json
import tempfile
from PIL import Image

class PostAPITestCase(TestCase):
    """Test cases for Post API endpoints"""
    
    def setUp(self):
        """Set up test data and authenticated client"""
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1', 
                                            password='testpass123',
                                            email='test1@example.com')
        self.user2 = User.objects.create_user(username='testuser2', 
                                            password='testpass123',
                                            email='test2@example.com')
        
        # Create university and company
        self.university = University.objects.create(
            name='Test University',
            description='A test university',
            is_private=False
        )
        self.university.admins.add(self.user1)
        
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            industry='Photography',
            is_private=True
        )
        self.company.admins.add(self.user2)
        
        # Create department
        self.department = Department.objects.create(
            name='Photography Department',
            university=self.university,
            description='Department for photographers'
        )
        
        # Create membership
        self.membership = OrganizationMembership.objects.create(
            university=self.university,
            user=self.user2,
            department=self.department,
            role='Student'
        )
        
        # Create test posts
        self.public_post = Post.objects.create(
            title='Public Test Post',
            content='This is a public post for testing',
            author=self.user1,
            is_private=False
        )
        
        self.private_post = Post.objects.create(
            title='Private University Post',
            content='This is a private university post',
            author=self.user1,
            university=self.university,
            department=self.department,
            is_private=True
        )
        
        self.company_post = Post.objects.create(
            title='Company Post',
            content='This is a company post',
            author=self.user2,
            company=self.company,
            is_private=True
        )
        
        # Set up API client
        self.client = APIClient()
        
    def test_post_list_anonymous(self):
        """Test that anonymous users can only see public posts"""
        response = self.client.get(reverse('post-list'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)  # Only the public post
        self.assertEqual(data['results'][0]['title'], 'Public Test Post')
    
    def test_post_list_authenticated(self):
        """Test that authenticated users see posts based on permissions"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('post-list'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # User2 should see: public post, private university post (as a member), and company post
        self.assertEqual(len(data['results']), 3)
        
    def test_post_detail_private(self):
        """Test access to private post details"""
        # Anonymous user should not access private post
        response = self.client.get(reverse('post-detail', args=[self.private_post.id]))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Member of university should access private post
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('post-detail', args=[self.private_post.id]))
        self.assertEqual(response.status_code, 200)
        
        # User not in company should not access private company post
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('post-detail', args=[self.company_post.id]))
        self.assertEqual(response.status_code, 403)
    
    def test_create_post(self):
        """Test creating a new post"""
        self.client.force_authenticate(user=self.user1)
        
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_img:
            # Create a test image
            image = Image.new('RGB', (100, 100), color='red')
            image.save(temp_img, format='JPEG')
            temp_img.seek(0)
            
            # Create post with image
            data = {
                'title': 'New Test Post',
                'content': 'This is a new test post with an image',
                'is_private': False,
                'image': temp_img
            }
            
            response = self.client.post(reverse('post-list'), data, format='multipart')
            self.assertEqual(response.status_code, 201)  # Created
            
            # Check post was created properly
            self.assertEqual(Post.objects.count(), 4)
            new_post = Post.objects.get(title='New Test Post')
            self.assertEqual(new_post.author, self.user1)
            self.assertIsNotNone(new_post.image)
    
    def test_post_like_unlike(self):
        """Test liking and unliking a post"""
        self.client.force_authenticate(user=self.user2)
        
        # Like a post
        response = self.client.post(reverse('post-like', args=[self.public_post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Like.objects.count(), 1)
        
        # Unlike the post
        response = self.client.post(reverse('post-unlike', args=[self.public_post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Like.objects.count(), 0)
    
    def test_post_share(self):
        """Test sharing a post"""
        self.client.force_authenticate(user=self.user2)
        
        data = {'shared_with': 'Twitter'}
        response = self.client.post(reverse('post-share', args=[self.public_post.id]), data)
        self.assertEqual(response.status_code, 200)
        
        # Verify share was created
        self.assertEqual(Share.objects.count(), 1)
        share = Share.objects.first()
        self.assertEqual(share.post, self.public_post)
        self.assertEqual(share.user, self.user2)
        self.assertEqual(share.shared_with, 'Twitter')
    
    def test_home_feed(self):
        """Test the home feed endpoint"""
        # Anonymous users can't access home feed
        response = self.client.get(reverse('post-home-feed'))
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
        # User with engagement should get feed
        self.client.force_authenticate(user=self.user2)
        
        # Create some engagement
        Like.objects.create(post=self.public_post, user=self.user2)
        Comment.objects.create(post=self.public_post, author=self.user2, content='Test comment')
        
        response = self.client.get(reverse('post-home-feed'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        # Public post should be prioritized due to engagement
        self.assertEqual(data[0]['id'], self.public_post.id)

class CommentAPITestCase(TestCase):
    """Test cases for Comment API endpoints"""
    
    def setUp(self):
        # Create test user and post
        self.user = User.objects.create_user(username='testuser', 
                                          password='testpass123')
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post',
            author=self.user
        )
        
        # Create a comment
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='This is a test comment'
        )
        
        # Set up API client
        self.client = APIClient()
        
    def test_list_comments(self):
        """Test listing comments"""
        response = self.client.get(reverse('comment-list'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['content'], 'This is a test comment')
    
    def test_create_comment(self):
        """Test creating a comment"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'post': self.post.id,
            'content': 'This is a new comment'
        }
        
        response = self.client.post(reverse('comment-list'), data)
        self.assertEqual(response.status_code, 201)
        
        self.assertEqual(Comment.objects.count(), 2)
        new_comment = Comment.objects.get(content='This is a new comment')
        self.assertEqual(new_comment.author, self.user)
        self.assertEqual(new_comment.post, self.post)
    
    def test_update_comment(self):
        """Test updating a comment"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'content': 'Updated comment content',
            'post': self.post.id
        }
        
        response = self.client.patch(reverse('comment-detail', args=[self.comment.id]), data)
        self.assertEqual(response.status_code, 200)
        
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Updated comment content')
    
    def test_delete_comment(self):
        """Test deleting a comment"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(reverse('comment-detail', args=[self.comment.id]))
        self.assertEqual(response.status_code, 204)
        
        self.assertEqual(Comment.objects.count(), 0)

class LikeShareAPITestCase(TestCase):
    """Test cases for Like and Share API endpoints"""
    
    def setUp(self):
        # Create test users and post
        self.user1 = User.objects.create_user(username='testuser1', 
                                            password='testpass123')
        self.user2 = User.objects.create_user(username='testuser2', 
                                            password='testpass123')
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post',
            author=self.user1
        )
        
        # Create like and share
        self.like = Like.objects.create(
            post=self.post,
            user=self.user1
        )
        
        self.share = Share.objects.create(
            post=self.post,
            user=self.user1,
            shared_with='Facebook'
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_list_likes(self):
        """Test listing likes"""
        response = self.client.get(reverse('like-list'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['user']['username'], 'testuser1')
    
    def test_filter_likes(self):
        """Test filtering likes by post"""
        response = self.client.get(f"{reverse('like-list')}?post={self.post.id}")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        
        # Create another post and like
        other_post = Post.objects.create(
            title='Other Post',
            content='This is another post',
            author=self.user2
        )
        
        Like.objects.create(
            post=other_post,
            user=self.user2
        )
        
        # Filter by first post
        response = self.client.get(f"{reverse('like-list')}?post={self.post.id}")
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['post'], self.post.id)
    
    def test_list_shares(self):
        """Test listing shares"""
        response = self.client.get(reverse('share-list'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['shared_with'], 'Facebook')
    
    def test_filter_shares(self):
        """Test filtering shares by user"""
        response = self.client.get(f"{reverse('share-list')}?user={self.user1.id}")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        
        # Create another share by user2
        Share.objects.create(
            post=self.post,
            user=self.user2,
            shared_with='Twitter'
        )
        
        # Filter by user1
        response = self.client.get(f"{reverse('share-list')}?user={self.user1.id}")
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['user']['username'], 'testuser1') 