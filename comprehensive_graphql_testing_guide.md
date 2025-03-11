# PhotoCampus GraphQL Testing Guide

This step-by-step guide will help you test all the features of the PhotoCampus platform using GraphQL queries and mutations. Each section builds on the previous ones to demonstrate the complete workflow, mirroring the exact flow of the automated tests.

## Prerequisites

- You need to have the PhotoCampus backend server running locally
- Access to the GraphQL endpoint (typically at http://localhost:8000/graphql/)
- A tool to make GraphQL requests (like the GraphQL Playground, Postman, Insomnia, or even curl)
- A way to store and reuse tokens, IDs, and other values between requests

## Test Data Management

Throughout this guide, you'll need to store and reuse various values like authentication tokens and IDs. Create a simple tracking system to store:

```
- token: JWT authentication token
- refresh_token: JWT refresh token (if used)
- username: Your test username
- university_id: ID of the created university
- department_id: ID of the created department
- company_id: ID of the created company
- post_ids: Map of different post IDs by type
- comment_id: ID of the created comment
- invitation_tokens: Tokens for various invitations
```

## 1. Authentication and User Management

### 1.1. Create a New User

First, create a unique test user:

```graphql
mutation CreateTestUser {
  createUser(
    username: "testuser[TIMESTAMP]"  # Add current timestamp to ensure uniqueness
    email: "testuser[TIMESTAMP]@example.com"
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
```

Record the username for later login.

### 1.2. Log In and Get Authentication Token

```graphql
mutation Login {
  tokenAuth(username: "YOUR_USERNAME", password: "securepassword123") {
    token
  }
}
```

Store the token for use in subsequent authenticated requests. All authenticated requests should include the header:
```
{
  "Authorization": "Bearer YOUR_TOKEN_HERE"
}
```

### 1.3. Verify Your Token

```graphql
mutation VerifyToken {
  verifyToken(token: "YOUR_TOKEN") {
    payload
  }
}
```

### 1.4. Get Current User Info

```graphql
query GetCurrentUser {
  me {
    id
    username
    email
    firstName
    lastName
  }
}
```

## 2. Organization Management

### 2.1. Create a University

```graphql
mutation CreateUniversity {
  createUniversity(
    name: "Test University"
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
```

Store the returned university ID.

### 2.2. Create a Department

```graphql
mutation CreateDepartment {
  createDepartment(
    name: "Computer Science"
    universityId: "UNIVERSITY_ID"  # Use the stored university ID
    description: "Department of Computer Science and Information Technology"
  ) {
    department {
      id
      name
      description
      university {
        id
        name
      }
    }
  }
}
```

Store the returned department ID.

### 2.3. Create a Company

```graphql
mutation CreateCompany {
  createCompany(
    name: "PhotoStudio Inc."
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
```

Store the returned company ID.

### 2.4. Query Organizations

```graphql
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
```

## 3. Invitation System

### 3.1. Create a University Invitation

```graphql
mutation InviteToUniversity {
  createInvitation(
    email: "newuser@example.com"
    universityId: "UNIVERSITY_ID"
    departmentId: "DEPARTMENT_ID"
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
```

Store the invitation token.

### 3.2. Create a Company Invitation

```graphql
mutation InviteToCompany {
  createInvitation(
    email: "colleague@example.com"
    companyId: "COMPANY_ID"
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
```

Store the invitation token.

## 4. Post Management

### 4.1. Create a Personal Post

```graphql
mutation CreatePersonalPost {
  createPost(
    title: "My First Personal Post"
    content: "This is a personal post created through GraphQL testing."
  ) {
    post {
      id
      title
      content
      author {
        username
      }
      createdAt
    }
  }
}
```

Store the post ID as "personal_post_id".

### 4.2. Create a University Post

```graphql
mutation CreateUniversityPost {
  createPost(
    title: "University Event Photos"
    content: "Photos from our annual graduation ceremony."
    universityId: "UNIVERSITY_ID"
    departmentId: "DEPARTMENT_ID"
    eventName: "Graduation Ceremony 2023"
    eventDate: "2023-06-15"
    location: "Main Campus"
    isPrivate: false
  ) {
    post {
      id
      title
      content
      eventName
      eventDate
      university {
        id
        name
      }
      department {
        id
        name
      }
      author {
        username
      }
    }
  }
}
```

Store the post ID as "university_post_id".

### 4.3. Create a Company Post

```graphql
mutation CreateCompanyPost {
  createPost(
    title: "Corporate Portfolio"
    content: "Recent photoshoot for our corporate clients."
    companyId: "COMPANY_ID"
    eventName: "Corporate Photoshoot"
    location: "Studio 3"
    isPrivate: true
  ) {
    post {
      id
      title
      content
      company {
        id
        name
      }
      author {
        username
      }
    }
  }
}
```

Store the post ID as "company_post_id".

### 4.4. Query All Posts

```graphql
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
        department {
          name
        }
      }
    }
  }
}
```

### 4.5. Search Posts

```graphql
query SearchPosts {
  searchPosts(searchTerm: "graduation", limit: 5) {
    id
    title
    content
    author {
      username
    }
    createdAt
  }
}
```

### 4.6. Update a Post

```graphql
mutation UpdatePost {
  updatePost(
    postId: "UNIVERSITY_POST_ID"
    title: "Updated University Post"
    content: "This content has been updated via GraphQL"
    eventName: "Updated Event Name"
    eventDate: "2023-07-15"
    location: "New Location"
    isPrivate: true
  ) {
    post {
      id
      title
      content
      eventName
      eventDate
      location
      isPrivate
    }
  }
}
```

## 5. Post Interactions

### 5.1. Add a Comment

```graphql
mutation AddComment {
  createComment(
    postId: "UNIVERSITY_POST_ID"
    content: "This is a test comment on the university post."
  ) {
    comment {
      id
      content
      createdAt
      author {
        username
      }
      post {
        id
        title
      }
    }
  }
}
```

Store the comment ID.

### 5.2. Like a Post

```graphql
mutation LikePost {
  likePost(postId: "UNIVERSITY_POST_ID") {
    like {
      id
      user {
        username
      }
      post {
        id
        title
      }
      createdAt
    }
  }
}
```

### 5.3. Share a Post

```graphql
mutation SharePost {
  sharePost(
    postId: "UNIVERSITY_POST_ID"
    sharedWith: "LinkedIn"
  ) {
    share {
      id
      sharedWith
      createdAt
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
```

### 5.4. Get Post with Statistics

```graphql
query PostWithStats {
  postsWithStats(limit: 5) {
    id
    title
    content
    author {
      username
    }
    comments {
      id
      content
      author {
        username
      }
      createdAt
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
      user {
        username
      }
    }
    likeCount
    commentCount
    shareCount
  }
}
```

### 5.5. Unlike a Post

```graphql
mutation UnlikePost {
  unlikePost(postId: "UNIVERSITY_POST_ID") {
    success
    message
  }
}
```

### 5.6. Delete a Comment

```graphql
mutation DeleteComment {
  deleteComment(commentId: "COMMENT_ID") {
    success
    message
  }
}
```

## 6. Advanced Queries

### 6.1. Filter Posts by Organization

```graphql
query FilterByOrganization {
  # Posts from a specific university
  universityPosts: allPosts(university_Id: "UNIVERSITY_ID", first: 5) {
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
  companyPosts: allPosts(company_Id: "COMPANY_ID", first: 5) {
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
```

### 6.2. Filter Posts by Department

```graphql
query FilterByDepartment {
  allPosts(department_Id: "DEPARTMENT_ID", first: 5) {
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
```

### 6.3. Get Organization Members

```graphql
query GetOrganizationMembers {
  # University members
  universityMemberships(university_Id: "UNIVERSITY_ID", first: 10) {
    edges {
      node {
        id
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
  companyMemberships(company_Id: "COMPANY_ID", first: 10) {
    edges {
      node {
        id
        role
        user {
          username
          email
        }
      }
    }
  }
}
```

## 7. Cleanup

### 7.1. Delete a Post

```graphql
mutation DeletePost {
  deletePost(postId: "PERSONAL_POST_ID") {
    success
    message
  }
}
```

## Helper Functions (Pseudocode)

If you're testing programmatically, you might want to implement helper functions similar to those in the test suite:

```javascript
// Example helper function for executing GraphQL queries
function executeQuery(query, variables = null, headers = null) {
  const requestHeaders = headers || {
    "Content-Type": "application/json"
  };
  
  const payload = { query };
  if (variables) {
    payload.variables = variables;
  }
  
  // Using fetch API as an example
  return fetch('http://localhost:8000/graphql/', {
    method: 'POST',
    headers: requestHeaders,
    body: JSON.stringify(payload)
  }).then(response => response.json());
}

// Example helper for authenticated requests
function getAuthenticatedHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `JWT ${storedToken}`
  };
}
```

## Working with IDs

GraphQL often returns IDs in a base64-encoded format. To extract the numeric ID:

```javascript
function extractNumericId(encodedId) {
  // Example: from "VW5pdmVyc2l0eU5vZGU6MQ==" to "1"
  const decoded = atob(encodedId);
  const match = decoded.match(/\d+$/);
  return match ? match[0] : null;
}
```

## Testing Tips

1. **Maintain State**: Store all IDs and tokens returned from operations for use in later tests.

2. **Sequential Testing**: Follow the testing flow in order as each step builds upon previous ones.

3. **Error Handling**: Always check for errors in responses for immediate debugging.

4. **Test Cleanup**: Run cleanup operations at the end to keep your test environment clean.

5. **Include Headers**: Remember to include authentication headers for all authenticated requests.

6. **Unique Test Data**: Use timestamps in usernames and emails to ensure uniqueness across test runs.

By following this guide, you'll be able to test the complete functionality of the PhotoCampus GraphQL API, exactly mirroring the automated test process. 