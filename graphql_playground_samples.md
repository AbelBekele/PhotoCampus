# GraphQL Playground Sample Queries & Mutations

This document provides ready-to-use sample queries and mutations you can paste directly into the GraphQL Playground.

## Authentication

```graphql
# Get a JWT token
mutation GetToken {
  tokenAuth(username: "yourusername", password: "yourpassword") {
    token
    refreshToken
  }
}

# Verify token
mutation VerifyToken {
  verifyToken(token: "your_token_here") {
    payload
  }
}

# Refresh token
mutation RefreshToken {
  refreshToken(refreshToken: "your_refresh_token_here") {
    token
    refreshToken
  }
}
```

## User Management

```graphql
# Create new user
mutation CreateUser {
  createUser(
    username: "newuser"
    email: "newuser@example.com"
    password: "securepassword123"
    firstName: "New"
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

# Get current user profile
query MyProfile {
  me {
    id
    username
    email
    firstName
    lastName
    profile {
      bio
      avatar
    }
    organizations {
      id
      name
      __typename
    }
  }
}

# Update user profile
mutation UpdateProfile {
  updateProfile(
    bio: "Photography enthusiast and CS student"
    avatar: "base64encodedimage..."
  ) {
    profile {
      bio
      avatar
    }
  }
}
```

## Organizations

```graphql
# Create university
mutation CreateUniversity {
  createUniversity(
    name: "Tech University"
    description: "A leading institution in technology education"
    location: "San Francisco, CA"
    website: "https://techuniversity.edu"
    logo: "base64encodedimage..."
  ) {
    university {
      id
      name
      description
      location
      createdAt
    }
  }
}

# Create department
mutation CreateDepartment {
  createDepartment(
    universityId: "university-id-here"
    name: "Computer Science"
    description: "Department of Computer Science and Software Engineering"
    headOfDepartment: "Dr. Jane Smith"
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

# Create company
mutation CreateCompany {
  createCompany(
    name: "ProPhoto Studio"
    description: "Professional photography services for all occasions"
    industry: "Photography"
    location: "New York, NY"
    website: "https://prophoto.example.com"
    logo: "base64encodedimage..."
  ) {
    company {
      id
      name
      description
      industry
      location
      createdAt
    }
  }
}

# Get university details
query UniversityDetails {
  university(id: "university-id-here") {
    id
    name
    description
    location
    website
    logo
    departments {
      id
      name
    }
    members {
      id
      username
      firstName
      lastName
    }
    posts {
      edges {
        node {
          id
          title
        }
      }
    }
  }
}

# Get all universities
query AllUniversities {
  universities(first: 10) {
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
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# Get all companies
query AllCompanies {
  companies(first: 10) {
    edges {
      node {
        id
        name
        industry
        location
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Invitations

```graphql
# Create invitation
mutation CreateInvitation {
  createInvitation(
    email: "student@example.com"
    organizationId: "university-id-here"
    organizationType: UNIVERSITY
    message: "Join our university community on PhotoCampus!"
  ) {
    invitation {
      id
      email
      status
      createdAt
      expiresAt
    }
  }
}

# Accept invitation
mutation AcceptInvitation {
  acceptInvitation(token: "invitation-token-here") {
    success
    message
    organization {
      id
      name
      __typename
    }
  }
}

# Decline invitation
mutation DeclineInvitation {
  declineInvitation(token: "invitation-token-here") {
    success
    message
  }
}

# List all invitations (admin only)
query ListInvitations {
  invitations(
    status: PENDING  # or ACCEPTED, DECLINED, EXPIRED
    first: 20
  ) {
    edges {
      node {
        id
        email
        status
        createdAt
        expiresAt
        organization {
          id
          name
          __typename
        }
      }
    }
  }
}
```

## Posts

```graphql
# Create post
mutation CreatePost {
  createPost(
    title: "Campus Spring Festival 2023"
    content: "Photos from this year's amazing spring festival on campus"
    organizationId: "university-id-here"
    organizationType: UNIVERSITY
    departmentId: "department-id-here"
    images: ["base64encodedimage1...", "base64encodedimage2..."]
    tags: ["festival", "spring", "campus"]
    location: "Main Campus Quad"
    eventDate: "2023-04-15T13:00:00Z"
    privacy: PUBLIC
  ) {
    post {
      id
      title
      content
      createdAt
      images {
        id
        url
      }
      tags
    }
  }
}

# Get posts with pagination
query GetPosts {
  posts(
    first: 10
    orderBy: "-created_at"
  ) {
    edges {
      node {
        id
        title
        content
        createdAt
        author {
          username
        }
        organization {
          id
          name
          __typename
        }
        images {
          id
          url
        }
        likesCount
        commentsCount
        tags
        liked
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# Get posts by organization
query OrganizationPosts {
  posts(
    organizationId: "organization-id-here"
    first: 10
  ) {
    edges {
      node {
        id
        title
        createdAt
        images {
          id
          url
        }
        likesCount
        commentsCount
      }
    }
  }
}

# Get post details with comments
query PostDetails {
  post(id: "post-id-here") {
    id
    title
    content
    createdAt
    author {
      username
      firstName
      lastName
    }
    organization {
      id
      name
      __typename
    }
    department {
      id
      name
    }
    images {
      id
      url
    }
    comments {
      edges {
        node {
          id
          content
          createdAt
          author {
            username
          }
        }
      }
    }
    likesCount
    commentsCount
    sharesCount
    liked
    tags
    location
    eventDate
  }
}

# Get personalized home feed
query HomeFeed {
  homeFeed(first: 20) {
    edges {
      node {
        id
        title
        content
        createdAt
        author {
          username
          firstName
          lastName
        }
        organization {
          id
          name
          __typename
        }
        images {
          id
          url
        }
        likesCount
        commentsCount
        tags
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# Search posts
query SearchPosts {
  posts(
    search: "graduation"
    first: 10
  ) {
    edges {
      node {
        id
        title
        content
        images {
          id
          url
        }
      }
    }
  }
}
```

## Interactions

```graphql
# Like a post
mutation LikePost {
  likePost(postId: "post-id-here") {
    post {
      id
      likesCount
      liked
    }
  }
}

# Unlike a post
mutation UnlikePost {
  unlikePost(postId: "post-id-here") {
    post {
      id
      likesCount
      liked
    }
  }
}

# Add comment
mutation AddComment {
  createComment(
    postId: "post-id-here"
    content: "This looks amazing! Love the photos from the event."
  ) {
    comment {
      id
      content
      createdAt
      author {
        username
      }
    }
  }
}

# Delete comment
mutation DeleteComment {
  deleteComment(commentId: "comment-id-here") {
    success
  }
}

# Share post
mutation SharePost {
  sharePost(
    postId: "post-id-here"
    platform: "facebook"
  ) {
    success
    shareUrl
  }
}
```

## Advanced Queries

```graphql
# Get users by department
query DepartmentUsers {
  users(departmentId: "department-id-here", first: 20) {
    edges {
      node {
        id
        username
        firstName
        lastName
        profile {
          avatar
        }
      }
    }
  }
}

# Get posts with specific tags
query PostsByTags {
  posts(tags: ["graduation", "2023"], first: 15) {
    edges {
      node {
        id
        title
        tags
        images {
          id
          url
        }
      }
    }
  }
}

# Get trending posts (most liked/commented in last week)
query TrendingPosts {
  trendingPosts(timeframe: WEEK, first: 10) {
    edges {
      node {
        id
        title
        likesCount
        commentsCount
        images {
          id
          url
        }
        organization {
          name
        }
      }
    }
  }
}
```

For more detailed information about using the GraphQL API, see the [GraphQL API Guide](graphql_api_guide.md). For comprehensive testing procedures, see the [GraphQL Testing Guide](comprehensive_graphql_testing_guide.md). 