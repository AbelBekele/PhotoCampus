import pytest
import json
import requests
from datetime import datetime
import base64
import re

# Configuration
GRAPHQL_URL = "http://localhost:8000/graphql/"
HEADERS = {"Content-Type": "application/json"}

# Test data storage for IDs and tokens
class TestData:
    token = None
    refresh_token = None
    university_id = None
    department_id = None
    company_id = None
    post_ids = {}
    comment_id = None
    invitation_tokens = {}


@pytest.fixture(scope="session")
def authenticated_headers():
    """Fixture that ensures we have authenticated headers for requests"""
    if not TestData.token:
        # Log in first to get the token
        login()
    
    return {
        "Content-Type": "application/json",
        "Authorization": f"JWT {TestData.token}"
    }


def execute_query(query, variables=None, headers=None):
    """Helper function to execute GraphQL queries"""
    request_headers = headers or HEADERS
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(GRAPHQL_URL, json=payload, headers=request_headers)
    return response.json()


# 1. Authentication and User Management
def test_create_user():
    """Test creating a new user"""
    # Generate unique username based on timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    username = f"testuser{timestamp}"
    
    mutation = """
    mutation CreateTestUser {
      createUser(
        username: "%s"
        email: "%s"
        password: "securepassword123"
        firstName: "Test"
        lastName: "User"
      ) {
        user {
          id
          username
          email
          firstName
          lastName
        }
      }
    }
    """ % (username, f"testuser{timestamp}@example.com")
    
    result = execute_query(mutation)
    assert "errors" not in result, f"Error creating user: {result.get('errors')}"
    assert result["data"]["createUser"]["user"]["username"] == username
    
    # Save username for login
    TestData.username = username


def login():
    """Log in and get authentication token"""
    mutation = """
    mutation Login {
      tokenAuth(username: "%s", password: "securepassword123") {
        token
      }
    }
    """ % TestData.username
    
    result = execute_query(mutation)
    assert "errors" not in result, f"Error logging in: {result.get('errors')}"
    
    TestData.token = result["data"]["tokenAuth"]["token"]


def test_verify_token(authenticated_headers):
    """Test verifying the authentication token"""
    mutation = """
    mutation VerifyToken {
      verifyToken(token: "%s") {
        payload
      }
    }
    """ % TestData.token
    
    result = execute_query(mutation)
    assert "errors" not in result, f"Error verifying token: {result.get('errors')}"
    assert "payload" in result["data"]["verifyToken"]


def test_get_current_user(authenticated_headers):
    """Test retrieving current user information"""
    query = """
    query GetCurrentUser {
      me {
        id
        username
        email
        firstName
        lastName
      }
    }
    """
    
    result = execute_query(query, headers=authenticated_headers)
    assert "errors" not in result, f"Error getting current user: {result.get('errors')}"
    assert result["data"]["me"]["username"] == TestData.username


# 2. Organization Management
def test_create_university(authenticated_headers):
    """Test creating a university"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    mutation = """
    mutation CreateUniversity {
      createUniversity(
        name: "Test University %s"
        description: "A test university for the PhotoCampus platform"
        location: "Test City, Country"
        foundedYear: 1990
        website: "https://testuniversity.edu"
        isPrivate: false
      ) {
        university {
          id
          name
          description
          location
          foundedYear
          website
          isPrivate
        }
      }
    }
    """ % timestamp
    
    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error creating university: {result.get('errors')}"
    
    university = result["data"]["createUniversity"]["university"]
    TestData.university_id = university["id"]
    assert "Test University" in university["name"]


def test_create_department(authenticated_headers):
    """Test creating a department within a university"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # Extract numeric ID from the encoded university ID
    university_id = extract_numeric_id(TestData.university_id)
    
    mutation = """
    mutation CreateDepartment {
      createDepartment(
        name: "Computer Science %s"
        universityId: %d
        description: "Department of Computer Science and Information Technology"
      ) {
        department {
          id
          name
          description
          university {
            name
          }
        }
      }
    }
    """ % (timestamp, university_id)

    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error creating department: {result.get('errors')}"
    
    # Save department ID for later tests
    TestData.department_id = result["data"]["createDepartment"]["department"]["id"]


def test_create_company(authenticated_headers):
    """Test creating a company"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    mutation = """
    mutation CreateCompany {
      createCompany(
        name: "PhotoStudio Inc. %s"
        description: "Professional photography studio"
        industry: "Photography"
        companySize: "Small (1-50)"
        website: "https://photostudio.example.com"
        isPrivate: true
      ) {
        company {
          id
          name
          description
          industry
          companySize
          website
          isPrivate
        }
      }
    }
    """ % timestamp
    
    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error creating company: {result.get('errors')}"
    
    company = result["data"]["createCompany"]["company"]
    TestData.company_id = company["id"]
    assert "PhotoStudio Inc." in company["name"]


def test_query_organizations(authenticated_headers):
    """Test querying organizations (universities and companies)"""
    query = """
    query GetOrganizations {
      allUniversities(first: 5) {
        edges {
          node {
            id
            name
            location
            departments {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
        }
      }
      allCompanies(first: 5) {
        edges {
          node {
            id
            name
            industry
          }
        }
      }
    }
    """

    result = execute_query(query, headers=authenticated_headers)
    assert "errors" not in result, f"Error querying organizations: {result.get('errors')}"


# 3. Invitation System
def test_create_university_invitation(authenticated_headers):
    """Test creating an invitation to a university"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"newuser{timestamp}@example.com"
    
    # Extract numeric IDs
    university_id = extract_numeric_id(TestData.university_id)
    department_id = extract_numeric_id(TestData.department_id)

    mutation = """
    mutation InviteToUniversity {
      createInvitation(
        email: "%s"
        universityId: %d
        departmentId: %d
        role: "Student"
        message: "Join our university on PhotoCampus!"
      ) {
        invitation {
          id
          token
          email
          status
          university {
            name
          }
          department {
            name
          }
        }
      }
    }
    """ % (email, university_id, department_id)

    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error creating university invitation: {result.get('errors')}"
    
    # Save invitation token for later use
    TestData.invitation_tokens["university"] = result["data"]["createInvitation"]["invitation"]["token"]


def test_create_company_invitation(authenticated_headers):
    """Test creating an invitation to a company"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"colleague{timestamp}@example.com"
    
    # Extract numeric ID
    company_id = extract_numeric_id(TestData.company_id)

    mutation = """
    mutation InviteToCompany {
      createInvitation(
        email: "%s"
        companyId: %d
        role: "Photographer"
        message: "Join our company on PhotoCampus!"
      ) {
        invitation {
          id
          token
          email
          status
          company {
            name
          }
        }
      }
    }
    """ % (email, company_id)

    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error creating company invitation: {result.get('errors')}"
    
    # Save invitation token for later use
    TestData.invitation_tokens["company"] = result["data"]["createInvitation"]["invitation"]["token"]


# 4. Post Management
def test_create_personal_post(authenticated_headers):
    """Test creating a personal post"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    mutation = """
    mutation CreatePersonalPost {
      createPost(
        title: "My First Post %s"
        content: "This is a personal post on PhotoCampus."
      ) {
        post {
          id
          title
          content
          author {
            username
          }
        }
      }
    }
    """ % timestamp
    
    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error creating personal post: {result.get('errors')}"
    
    post = result["data"]["createPost"]["post"]
    TestData.post_ids["personal"] = post["id"]
    assert "My First Post" in post["title"]


def test_create_university_post(authenticated_headers):
    """Test creating a university post"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Extract numeric IDs
    university_id = extract_numeric_id(TestData.university_id)
    department_id = extract_numeric_id(TestData.department_id)
    
    mutation = """
    mutation CreateUniversityPost {
      createPost(
        title: "University Event Photos %s"
        content: "Photos from our annual graduation ceremony."
        universityId: %d
        departmentId: %d
        location: "Main Campus"
        eventName: "Annual Graduation"
        eventDate: "2023-05-15"
      ) {
        post {
          id
          title
          content
          university {
            name
          }
          department {
            name
          }
          location
          eventName
          eventDate
        }
      }
    }
    """ % (timestamp, university_id, department_id)

    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error creating university post: {result.get('errors')}"
    
    # Save post ID for later tests
    TestData.post_ids["university"] = result["data"]["createPost"]["post"]["id"]


def test_create_company_post(authenticated_headers):
    """Test creating a company post"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Extract numeric ID
    company_id = extract_numeric_id(TestData.company_id)
    
    mutation = """
    mutation CreateCompanyPost {
      createPost(
        title: "Corporate Portfolio %s"
        content: "Recent photoshoot for our corporate clients."
        companyId: %d
        location: "Studio 3"
        eventName: "Corporate Photoshoot"
        eventDate: "2023-06-15"
      ) {
        post {
          id
          title
          content
          company {
            name
          }
          location
          eventName
          eventDate
        }
      }
    }
    """ % (timestamp, company_id)

    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error creating company post: {result.get('errors')}"
    
    # Save post ID for later tests
    TestData.post_ids["company"] = result["data"]["createPost"]["post"]["id"]


def test_query_all_posts(authenticated_headers):
    """Test querying all posts"""
    query = """
    query GetAllPosts {
      allPosts(first: 10) {
        edges {
          node {
            id
            title
            content
            createdAt
            author {
              username
            }
            university {
              name
            }
            company {
              name
            }
          }
        }
      }
    }
    """
    
    result = execute_query(query, headers=authenticated_headers)
    assert "errors" not in result, f"Error querying all posts: {result.get('errors')}"
    assert "edges" in result["data"]["allPosts"]
    assert len(result["data"]["allPosts"]["edges"]) > 0


def test_search_posts(authenticated_headers):
    """Test searching for posts"""
    query = """
    query SearchPosts {
      searchPosts(searchTerm: "graduation", limit: 5) {
        id
        title
        content
        author {
          username
        }
      }
    }
    """
    
    result = execute_query(query, headers=authenticated_headers)
    assert "errors" not in result, f"Error searching posts: {result.get('errors')}"
    # Note: This might return empty if no posts match, which is still valid


def test_update_post(authenticated_headers):
    """Test updating a post"""
    # Use the personal post we created earlier
    post_id_encoded = TestData.post_ids["personal"]
    post_id = extract_numeric_id(post_id_encoded)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    mutation = """
    mutation UpdatePost {
      updatePost(
        postId: %d
        title: "Updated Post Title %s"
        content: "This content has been updated via GraphQL"
        isPrivate: true
      ) {
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
    """ % (post_id, timestamp)

    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error updating post: {result.get('errors')}"


# 5. Post Interactions
def test_add_comment(authenticated_headers):
    """Test adding a comment to a post"""
    # Use the personal post if university post creation failed
    post_id_key = "personal" if "university" not in TestData.post_ids else "university"
    post_id_encoded = TestData.post_ids[post_id_key]
    post_id = extract_numeric_id(post_id_encoded)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    mutation = """
    mutation AddComment {
      createComment(
        postId: %d
        content: "This is a test comment %s"
      ) {
        comment {
          id
          content
          author {
            username
          }
        }
      }
    }
    """ % (post_id, timestamp)
    
    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error adding comment: {result.get('errors')}"
    
    # Save comment ID for later deletion test
    TestData.comment_id = result["data"]["createComment"]["comment"]["id"]


def test_like_post(authenticated_headers):
    """Test liking a post"""
    # Use the personal post if university post creation failed
    post_id_key = "personal" if "university" not in TestData.post_ids else "university"
    post_id_encoded = TestData.post_ids[post_id_key]
    post_id = extract_numeric_id(post_id_encoded)
    
    mutation = """
    mutation LikePost {
      likePost(postId: %d) {
        like {
          id
          post {
            id
            title
          }
          user {
            username
          }
        }
      }
    }
    """ % post_id
    
    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error liking post: {result.get('errors')}"


def test_share_post(authenticated_headers):
    """Test sharing a post"""
    # Use the personal post if university post creation failed
    post_id_key = "personal" if "university" not in TestData.post_ids else "university"
    post_id_encoded = TestData.post_ids[post_id_key]
    post_id = extract_numeric_id(post_id_encoded)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    mutation = """
    mutation SharePost {
      sharePost(
        postId: %d
        sharedWith: "EMAIL_%s"
      ) {
        share {
          id
          sharedWith
          user {
            username
          }
          post {
            id
            title
          }
        }
      }
    }
    """ % (post_id, timestamp)
    
    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error sharing post: {result.get('errors')}"


def test_post_with_stats(authenticated_headers):
    """Test retrieving a post with its statistics"""
    query = """
    query PostWithStats {
      postsWithStats(limit: 1) {
        id
        title
        content
        author {
          username
        }
        comments {
          edges {
            node {
              id
              content
              author {
                username
              }
              createdAt
            }
          }
        }
        likes {
          edges {
            node {
              id
              user {
                username
              }
            }
          }
        }
        shares {
          edges {
            node {
              id
              sharedWith
              user {
                username
              }
            }
          }
        }
      }
    }
    """

    result = execute_query(query, headers=authenticated_headers)
    assert "errors" not in result, f"Error getting post with stats: {result.get('errors')}"


def test_unlike_post(authenticated_headers):
    """Test unliking a post"""
    # Use the personal post if university post creation failed
    post_id_key = "personal" if "university" not in TestData.post_ids else "university"
    post_id_encoded = TestData.post_ids[post_id_key]
    post_id = extract_numeric_id(post_id_encoded)
    
    mutation = """
    mutation UnlikePost {
      unlikePost(postId: %d) {
        success
      }
    }
    """ % post_id
    
    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error unliking post: {result.get('errors')}"


def test_delete_comment(authenticated_headers):
    """Test deleting a comment"""
    comment_id = extract_numeric_id(TestData.comment_id)

    mutation = """
    mutation DeleteComment {
      deleteComment(commentId: %d) {
        success
        message
      }
    }
    """ % comment_id

    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error deleting comment: {result.get('errors')}"


# 6. Advanced Queries
def test_filter_posts_by_organization(authenticated_headers):
    """Test filtering posts by organization"""
    university_id = extract_numeric_id(TestData.university_id)
    company_id = extract_numeric_id(TestData.company_id)
    
    query = """
    query FilterByOrganization {
      # Posts from a specific university
      universityPosts: allPosts(universityId: "%d", first: 5) {
        edges {
          node {
            id
            title
            university {
              name
            }
          }
        }
      }

      # Posts from a specific company
      companyPosts: allPosts(companyId: "%d", first: 5) {
        edges {
          node {
            id
            title
            company {
              name
            }
          }
        }
      }
    }
    """ % (university_id, company_id)

    result = execute_query(query, headers=authenticated_headers)
    assert "errors" not in result, f"Error filtering posts by organization: {result.get('errors')}"


def test_filter_posts_by_department(authenticated_headers):
    """Test filtering posts by department"""
    department_id = extract_numeric_id(TestData.department_id)
    
    query = """
    query FilterByDepartment {
      allPosts(departmentId: "%d", first: 5) {
        edges {
          node {
            id
            title
            department {
              name
            }
            university {
              name
            }
          }
        }
      }
    }
    """ % department_id

    result = execute_query(query, headers=authenticated_headers)
    assert "errors" not in result, f"Error filtering posts by department: {result.get('errors')}"


def test_get_organization_members(authenticated_headers):
    """Test getting organization members"""
    # We need to get university and company names instead of IDs
    university_name = "Test University" # Standard name used in the test
    company_name = "Test Company" # Standard name used in the test
    
    query = """
    query GetOrganizationMembers {
      # University members
      universityMembers: organizationMembers(university_Name: "%s", first: 10) {
        edges {
          node {
            role
            user {
              username
              email
            }
            department {
              name
            }
          }
        }
      }

      # Company members
      companyMembers: organizationMembers(company_Name: "%s", first: 10) {
        edges {
          node {
            role
            user {
              username
              email
            }
          }
        }
      }
    }
    """ % (university_name, company_name)

    result = execute_query(query, headers=authenticated_headers)
    assert "errors" not in result, f"Error getting organization members: {result.get('errors')}"


# 7. Cleanup
def test_delete_post(authenticated_headers):
    """Test deleting a post"""
    # Delete the personal post we created earlier
    post_id_encoded = TestData.post_ids["personal"]
    post_id = extract_numeric_id(post_id_encoded)
    
    mutation = """
    mutation DeletePost {
      deletePost(postId: %d) {
        success
        message
      }
    }
    """ % post_id
    
    result = execute_query(mutation, headers=authenticated_headers)
    assert "errors" not in result, f"Error deleting post: {result.get('errors')}"
    assert result["data"]["deletePost"]["success"] is True


def extract_numeric_id(encoded_id):
    """Extract the numeric ID from a base64 encoded GraphQL ID."""
    if encoded_id is None:
        return None
    
    try:
        # Try to decode the base64 string
        decoded = base64.b64decode(encoded_id).decode('utf-8')
        # Extract numeric ID using regex
        match = re.search(r':(\d+)$', decoded)
        if match:
            return int(match.group(1))
    except:
        pass
    
    # Fallback: if the ID is already numeric or extraction fails
    try:
        return int(encoded_id)
    except:
        return encoded_id
