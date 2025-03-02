import requests
import json
import pytest
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# GraphQL API endpoint
API_URL = os.getenv('GRAPHQL_API_URL', 'http://localhost:8000/graphql/')

# Authentication Queries
LOGIN = """
mutation TokenAuth($username: String!, $password: String!) {
  tokenAuth(username: $username, password: $password) {
    token
    refreshToken
  }
}
"""

VERIFY_TOKEN = """
mutation VerifyToken($token: String!) {
  verifyToken(token: $token) {
    payload
  }
}
"""

REFRESH_TOKEN = """
mutation RefreshToken($refreshToken: String!) {
  refreshToken(refreshToken: $refreshToken) {
    token
    refreshToken
  }
}
"""

# User Management Queries
CREATE_USER = """
mutation CreateUser($username: String!, $email: String!, $password: String!, $firstName: String, $lastName: String) {
  createUser(username: $username, email: $email, password: $password, firstName: $firstName, lastName: $lastName) {
    user {
      id
      username
      email
      firstName
      lastName
    }
  }
}
"""

GET_ME = """
query {
  me {
    id
    username
    email
    firstName
    lastName
  }
}
"""

# Posts Queries
QUERY_POSTS = """
{
  allPosts {
    edges {
      node {
        id
        title
        content
        createdAt
        author {
          username
        }
      }
    }
  }
}
"""

QUERY_POSTS_WITH_STATS = """
{
  postsWithStats(limit: 5) {
    id
    title
    content
    createdAt
    author {
      username
    }
    comments {
      id
      content
      author {
        username
      }
    }
    likes {
      id
      user {
        username
      }
    }
    shares {
      id
      sharedWith
    }
  }
}
"""

SEARCH_POSTS = """
query SearchPosts($term: String!) {
  searchPosts(searchTerm: $term, limit: 5) {
    id
    title
    content
    author {
      username
    }
  }
}
"""

# Post Management Mutations
CREATE_POST = """
mutation CreatePost($title: String!, $content: String!, $isPrivate: Boolean) {
  createPost(title: $title, content: $content, isPrivate: $isPrivate) {
    post {
      id
      title
      content
      isPrivate
      author {
        username
      }
    }
  }
}
"""

UPDATE_POST = """
mutation UpdatePost($postId: ID!, $title: String, $content: String, $isPrivate: Boolean) {
  updatePost(postId: $postId, title: $title, content: $content, isPrivate: $isPrivate) {
    post {
      id
      title
      content
      isPrivate
    }
    success
    message
  }
}
"""

DELETE_POST = """
mutation DeletePost($postId: ID!) {
  deletePost(postId: $postId) {
    success
    message
  }
}
"""

# Comment Mutations
CREATE_COMMENT = """
mutation CreateComment($postId: ID!, $content: String!) {
  createComment(postId: $postId, content: $content) {
    comment {
      id
      content
      author {
        username
      }
      post {
        title
      }
    }
  }
}
"""

DELETE_COMMENT = """
mutation DeleteComment($commentId: ID!) {
  deleteComment(commentId: $commentId) {
    success
    message
  }
}
"""

# Like Mutations
LIKE_POST = """
mutation LikePost($postId: ID!) {
  likePost(postId: $postId) {
    like {
      id
      post {
        title
      }
      user {
        username
      }
    }
  }
}
"""

UNLIKE_POST = """
mutation UnlikePost($postId: ID!) {
  unlikePost(postId: $postId) {
    success
  }
}
"""

# Share Mutations
SHARE_POST = """
mutation SharePost($postId: ID!, $sharedWith: String!) {
  sharePost(postId: $postId, sharedWith: $sharedWith) {
    share {
      id
      post {
        title
      }
      user {
        username
      }
      sharedWith
    }
  }
}
"""

# GraphQL client function
def run_query(query, variables=None, token=None):
    """Send a GraphQL query to the server"""
    headers = {'Content-Type': 'application/json'}
    
    # Add authentication if token is provided
    if token:
        headers['Authorization'] = f'JWT {token}'
    
    data = {'query': query}
    if variables:
        data['variables'] = variables
    
    response = requests.post(API_URL, 
                           headers=headers, 
                           data=json.dumps(data))
    
    return response.json()

# Pytest fixtures
@pytest.fixture(scope="session")
def test_username():
    """Test username - can be overridden with environment variable TEST_USERNAME"""
    return os.getenv('TEST_USERNAME', 'testuser')

@pytest.fixture(scope="session")
def test_email():
    """Test email - can be overridden with environment variable TEST_EMAIL"""
    return os.getenv('TEST_EMAIL', 'testuser@example.com')

@pytest.fixture(scope="session")
def test_password():
    """Test password - can be overridden with environment variable TEST_PASSWORD"""
    return os.getenv('TEST_PASSWORD', 'securepassword123')

@pytest.fixture(scope="session")
def test_user(test_username, test_email, test_password):
    """Create a test user and yield the user details"""
    # Skip user creation if TEST_SKIP_USER_CREATION is set
    if os.getenv('TEST_SKIP_USER_CREATION', 'false').lower() == 'true':
        return {'username': test_username, 'email': test_email}
    
    variables = {
        "username": test_username,
        "email": test_email,
        "password": test_password,
        "firstName": "Test",
        "lastName": "User"
    }
    
    result = run_query(CREATE_USER, variables)
    
    if 'errors' in result:
        # If user exists, just return the username and email
        return {'username': test_username, 'email': test_email}
    
    return result.get('data', {}).get('createUser', {}).get('user', 
                                         {'username': test_username, 'email': test_email})

@pytest.fixture(scope="session")
def auth_token(test_user, test_username, test_password):
    """Get authentication token for the test user"""
    result = run_query(LOGIN, {
        "username": test_username,
        "password": test_password
    })
    
    token = result.get('data', {}).get('tokenAuth', {}).get('token')
    if not token:
        pytest.skip("Could not obtain authentication token")
    
    return token

@pytest.fixture(scope="function")
def test_post(auth_token):
    """Create a test post for use in tests and delete it after the test"""
    variables = {
        "title": "Test Post for PyTest",
        "content": "This is a test post created by PyTest",
        "isPrivate": False
    }
    
    result = run_query(CREATE_POST, variables, auth_token)
    post = result.get('data', {}).get('createPost', {}).get('post')
    
    if not post:
        pytest.skip("Could not create test post")
    
    # Return the post for test use
    yield post
    
    # Delete the post after the test
    run_query(DELETE_POST, {"postId": post['id']}, auth_token)

@pytest.fixture(scope="function")
def test_comment(test_post, auth_token):
    """Create a test comment on the test post and delete it after the test"""
    variables = {
        "postId": test_post['id'],
        "content": "This is a test comment created by PyTest"
    }
    
    result = run_query(CREATE_COMMENT, variables, auth_token)
    comment = result.get('data', {}).get('createComment', {}).get('comment')
    
    if not comment:
        pytest.skip("Could not create test comment")
    
    # Return the comment for test use
    yield comment
    
    # Delete the comment after the test
    run_query(DELETE_COMMENT, {"commentId": comment['id']}, auth_token)

# Authentication Tests
@pytest.mark.authentication
def test_login(test_username, test_password):
    """Test login functionality"""
    result = run_query(LOGIN, {
        "username": test_username,
        "password": test_password
    })
    
    assert 'errors' not in result, f"Login failed: {result.get('errors')}"
    assert 'data' in result
    assert 'tokenAuth' in result['data']
    assert 'token' in result['data']['tokenAuth']
    assert 'refreshToken' in result['data']['tokenAuth']

@pytest.mark.authentication
def test_token_verification(auth_token):
    """Test token verification"""
    result = run_query(VERIFY_TOKEN, {"token": auth_token})
    
    assert 'errors' not in result, f"Token verification failed: {result.get('errors')}"
    assert 'data' in result
    assert 'verifyToken' in result['data']
    assert 'payload' in result['data']['verifyToken']

@pytest.mark.authentication
def test_get_current_user(auth_token):
    """Test getting current user details"""
    result = run_query(GET_ME, token=auth_token)
    
    assert 'errors' not in result, f"Get current user failed: {result.get('errors')}"
    assert 'data' in result
    assert 'me' in result['data']
    assert 'id' in result['data']['me']
    assert 'username' in result['data']['me']
    assert 'email' in result['data']['me']

# Post Query Tests
@pytest.mark.posts
def test_query_all_posts():
    """Test querying all posts"""
    result = run_query(QUERY_POSTS)
    
    assert 'errors' not in result, f"Query all posts failed: {result.get('errors')}"
    assert 'data' in result
    assert 'allPosts' in result['data']
    assert 'edges' in result['data']['allPosts']

@pytest.mark.posts
def test_query_posts_with_stats():
    """Test querying posts with stats"""
    result = run_query(QUERY_POSTS_WITH_STATS)
    
    assert 'errors' not in result, f"Query posts with stats failed: {result.get('errors')}"
    assert 'data' in result
    assert 'postsWithStats' in result['data']

@pytest.mark.posts
@pytest.mark.parametrize("search_term", ["test", "photo", "post"])
def test_search_posts(search_term):
    """Test searching posts with different terms"""
    result = run_query(SEARCH_POSTS, {"term": search_term})
    
    assert 'errors' not in result, f"Search posts failed: {result.get('errors')}"
    assert 'data' in result
    assert 'searchPosts' in result['data']

# Post Management Tests
@pytest.mark.posts
def test_create_post(auth_token):
    """Test creating a post"""
    variables = {
        "title": "Created Post for Test",
        "content": "This is a post created specifically for testing post creation",
        "isPrivate": False
    }
    
    result = run_query(CREATE_POST, variables, auth_token)
    
    assert 'errors' not in result, f"Create post failed: {result.get('errors')}"
    assert 'data' in result
    assert 'createPost' in result['data']
    assert 'post' in result['data']['createPost']
    assert 'id' in result['data']['createPost']['post']
    
    # Clean up
    post_id = result['data']['createPost']['post']['id']
    run_query(DELETE_POST, {"postId": post_id}, auth_token)

@pytest.mark.posts
def test_update_post(test_post, auth_token):
    """Test updating a post"""
    variables = {
        "postId": test_post['id'],
        "title": "Updated Post Title",
        "content": "This content has been updated for testing",
        "isPrivate": True
    }
    
    result = run_query(UPDATE_POST, variables, auth_token)
    
    assert 'errors' not in result, f"Update post failed: {result.get('errors')}"
    assert 'data' in result
    assert 'updatePost' in result['data']
    assert 'post' in result['data']['updatePost']
    assert 'success' in result['data']['updatePost']
    assert result['data']['updatePost']['success'] is True
    assert 'message' in result['data']['updatePost']
    
    # Verify the updated post
    assert result['data']['updatePost']['post']['title'] == variables['title']
    assert result['data']['updatePost']['post']['content'] == variables['content']
    assert result['data']['updatePost']['post']['isPrivate'] is True

@pytest.mark.posts
def test_delete_post(auth_token):
    """Test deleting a post"""
    # First create a post to delete
    variables = {
        "title": "Post to Delete",
        "content": "This post will be deleted",
        "isPrivate": False
    }
    
    create_result = run_query(CREATE_POST, variables, auth_token)
    post_id = create_result['data']['createPost']['post']['id']
    
    # Delete the post
    delete_result = run_query(DELETE_POST, {"postId": post_id}, auth_token)
    
    assert 'errors' not in delete_result, f"Delete post failed: {delete_result.get('errors')}"
    assert 'data' in delete_result
    assert 'deletePost' in delete_result['data']
    assert 'success' in delete_result['data']['deletePost']
    assert delete_result['data']['deletePost']['success'] is True
    assert 'message' in delete_result['data']['deletePost']

# Comment Tests
@pytest.mark.comments
def test_create_comment(test_post, auth_token):
    """Test creating a comment on a post"""
    variables = {
        "postId": test_post['id'],
        "content": "This is a test comment"
    }
    
    result = run_query(CREATE_COMMENT, variables, auth_token)
    
    assert 'errors' not in result, f"Create comment failed: {result.get('errors')}"
    assert 'data' in result
    assert 'createComment' in result['data']
    assert 'comment' in result['data']['createComment']
    assert 'id' in result['data']['createComment']['comment']
    
    # Clean up
    comment_id = result['data']['createComment']['comment']['id']
    run_query(DELETE_COMMENT, {"commentId": comment_id}, auth_token)

@pytest.mark.comments
def test_delete_comment(test_comment, auth_token):
    """Test deleting a comment"""
    result = run_query(DELETE_COMMENT, {"commentId": test_comment['id']}, auth_token)
    
    assert 'errors' not in result, f"Delete comment failed: {result.get('errors')}"
    assert 'data' in result
    assert 'deleteComment' in result['data']
    assert 'success' in result['data']['deleteComment']
    assert result['data']['deleteComment']['success'] is True
    assert 'message' in result['data']['deleteComment']

# Like Tests
@pytest.mark.likes
def test_like_and_unlike_post(test_post, auth_token):
    """Test liking and unliking a post"""
    # Like the post
    like_result = run_query(LIKE_POST, {"postId": test_post['id']}, auth_token)
    
    assert 'errors' not in like_result, f"Like post failed: {like_result.get('errors')}"
    assert 'data' in like_result
    assert 'likePost' in like_result['data']
    assert 'like' in like_result['data']['likePost']
    assert 'id' in like_result['data']['likePost']['like']
    
    # Unlike the post
    unlike_result = run_query(UNLIKE_POST, {"postId": test_post['id']}, auth_token)
    
    assert 'errors' not in unlike_result, f"Unlike post failed: {unlike_result.get('errors')}"
    assert 'data' in unlike_result
    assert 'unlikePost' in unlike_result['data']
    assert 'success' in unlike_result['data']['unlikePost']
    assert unlike_result['data']['unlikePost']['success'] is True

# Share Test
@pytest.mark.shares
@pytest.mark.parametrize("platform", ["Twitter", "Facebook", "Instagram", "LinkedIn"])
def test_share_post(test_post, auth_token, platform):
    """Test sharing a post to different platforms"""
    variables = {
        "postId": test_post['id'],
        "sharedWith": platform
    }
    
    result = run_query(SHARE_POST, variables, auth_token)
    
    assert 'errors' not in result, f"Share post failed: {result.get('errors')}"
    assert 'data' in result
    assert 'sharePost' in result['data']
    assert 'share' in result['data']['sharePost']
    assert 'id' in result['data']['sharePost']['share']
    assert 'sharedWith' in result['data']['sharePost']['share']
    assert result['data']['sharePost']['share']['sharedWith'] == platform

if __name__ == "__main__":
    print("This script is designed to be run with pytest.")
    print("Run 'pytest test_graphql.py -v' to execute the tests.") 