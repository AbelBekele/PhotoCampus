# PhotoCampus GraphQL Testing Guide

This step-by-step guide will help you test all the features of the PhotoCampus platform using GraphQL queries and mutations. Each section builds on the previous ones to demonstrate the complete workflow.

## Prerequisites

- You need to have the PhotoCampus backend server running
- Access to the GraphQL endpoint (typically at http://localhost:8000/graphql/)
- The ability to store and use the JWT token between requests

## 1. Authentication and User Management

### 1.1. Create a New User

```graphql
mutation CreateTestUser {
  createUser(
    username: "testuser"
    email: "testuser@example.com"
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

### 1.2. Log In and Get Authentication Token

```graphql
mutation Login {
  tokenAuth(username: "testuser", password: "securepassword123") {
    token
    refreshToken
  }
}
```

Copy the token from the response. You'll need to include it in an HTTP header for authenticated requests:
```
{
  "Authorization": "JWT your_token_here"
}
```

### 1.3. Verify Your Token

```graphql
mutation VerifyToken {
  verifyToken(token: "your_token_here") {
    payload
  }
}
```

### 1.4. Get Current User Info (Authenticated)

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

Save the returned university ID for later use.

### 2.2. Create a Department

```graphql
mutation CreateDepartment {
  createDepartment(
    name: "Computer Science"
    universityId: "1"  # Replace with the actual university ID from the previous step
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
```

Save the returned department ID.

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

Save the returned company ID.

### 2.4. Query Organizations

```graphql
query GetOrganizations {
  universities(first: 5) {
    edges {
      node {
        id
        name
        location
        departments {
          id
          name
        }
      }
    }
  }
  companies(first: 5) {
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

### 3.1. Create an Invitation to University

```graphql
mutation InviteToUniversity {
  createInvitation(
    email: "newuser@example.com"
    universityId: "1"  # Replace with actual university ID
    departmentId: "1"  # Replace with actual department ID
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

Save the invitation token.

### 3.2. Create an Invitation to Company

```graphql
mutation InviteToCompany {
  createInvitation(
    email: "colleague@example.com"
    companyId: "1"  # Replace with actual company ID
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

Save the invitation token.

### 3.3. Respond to Invitation (Accepting)

```graphql
mutation AcceptInvitation {
  respondToInvitation(
    invitationToken: "invitation_token_here"  # Replace with the actual token
    accept: true
  ) {
    success
    message
  }
}
```

### 3.4. Respond to Invitation (Declining)

```graphql
mutation DeclineInvitation {
  respondToInvitation(
    invitationToken: "invitation_token_here"  # Replace with another invitation token
    accept: false
  ) {
    success
    message
  }
}
```

## 4. Post Management

### 4.1. Create a Personal Post

```graphql
mutation CreatePersonalPost {
  createPost(
    title: "My First Post"
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
```

Save the post ID.

### 4.2. Create a University Post

```graphql
mutation CreateUniversityPost {
  createPost(
    title: "University Event Photos"
    content: "Photos from our annual graduation ceremony."
    universityId: "1"  # Replace with actual university ID
    departmentId: "1"  # Optional
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
        name
      }
      department {
        name
      }
    }
  }
}
```

Save this post ID.

### 4.3. Create a Company Post

```graphql
mutation CreateCompanyPost {
  createPost(
    title: "Corporate Portfolio"
    content: "Recent photoshoot for our corporate clients."
    companyId: "1"  # Replace with actual company ID
    eventName: "Corporate Photoshoot"
    location: "Studio 3"
    isPrivate: true
  ) {
    post {
      id
      title
      content
      company {
        name
      }
    }
  }
}
```

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
  }
}
```

### 4.6. Update a Post

```graphql
mutation UpdatePost {
  updatePost(
    postId: "1"  # Replace with actual post ID
    title: "Updated Post Title"
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
```

## 5. Post Interactions

### 5.1. Add a Comment

```graphql
mutation AddComment {
  createComment(
    postId: "1"  # Replace with actual post ID
    content: "This is a great post! Thanks for sharing."
  ) {
    comment {
      id
      content
      createdAt
      author {
        username
      }
      post {
        title
      }
    }
  }
}
```

Save the comment ID.

### 5.2. Like a Post

```graphql
mutation LikePost {
  likePost(postId: "1") {  # Replace with actual post ID
    like {
      id
      user {
        username
      }
      post {
        title
      }
    }
  }
}
```

### 5.3. Share a Post

```graphql
mutation SharePost {
  sharePost(
    postId: "1"  # Replace with actual post ID
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
        title
      }
    }
  }
}
```

### 5.4. Get Post with Statistics

```graphql
query PostWithStats {
  postsWithStats(limit: 1) {
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
  }
}
```

### 5.5. Unlike a Post

```graphql
mutation UnlikePost {
  unlikePost(postId: "1") {  # Replace with actual post ID
    success
  }
}
```

### 5.6. Delete a Comment

```graphql
mutation DeleteComment {
  deleteComment(commentId: "1") {  # Replace with actual comment ID
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
  universityPosts: allPosts(university_Id: "1", first: 5) {  # Replace with actual university ID
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
  companyPosts: allPosts(company_Id: "1", first: 5) {  # Replace with actual company ID
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
  allPosts(department_Id: "1", first: 5) {  # Replace with actual department ID
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
  universityMemberships(university_Id: "1", first: 10) {  # Replace with actual university ID
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
  companyMemberships(company_Id: "1", first: 10) {  # Replace with actual company ID
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
```

## 7. Cleanup

### 7.1. Delete a Post

```graphql
mutation DeletePost {
  deletePost(postId: "1") {  # Replace with actual post ID
    success
    message
  }
}
```

## Testing Tips

1. **Use Variables**: Instead of hardcoding values in your queries, use GraphQL variables for more flexible testing.

2. **Sequential Testing**: Run these operations in the sequence shown to build on previous data.

3. **Error Handling**: Pay attention to error messages in responses for debugging issues.

4. **Permissions Testing**: Try accessing private posts or performing operations without proper authorization to test security.

5. **Batch Operations**: You can combine multiple queries or mutations in a single request where appropriate.

Remember to replace placeholder IDs with actual IDs returned from your operations. The GraphQL playground allows you to save queries for reuse during testing sessions. 