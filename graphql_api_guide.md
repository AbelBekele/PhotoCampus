# PhotoCampus GraphQL API Guide

This guide explains how to use the GraphQL API for post management and user interactions in the PhotoCampus application.

## Getting Started

The GraphQL API is accessible at `/graphql/`. You can use the GraphQL Playground interface at this endpoint for testing queries and mutations.

## Authentication

Most mutations require authentication using JSON Web Tokens (JWT). To authenticate:

1. Use the `tokenAuth` mutation to obtain a token:

```graphql
mutation {
  tokenAuth(username: "yourusername", password: "yourpassword") {
    token
    refreshToken
  }
}
```

2. Include the token in the Authorization header:

```
Authorization: JWT your_token_here
```

## User Management

### Creating a User

```graphql
mutation {
  createUser(
    username: "newuser",
    email: "newuser@example.com",
    password: "securepassword123",
    firstName: "New",
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

### User Login

```graphql
mutation {
  tokenAuth(username: "newuser", password: "securepassword123") {
    token
    refreshToken
    user {
      id
      username
      email
    }
  }
}
```

### User Profile

```graphql
query {
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
    }
  }
}
```

## Organization Management

### Create University

```graphql
mutation {
  createUniversity(
    name: "Sample University",
    description: "A leading educational institution",
    location: "New York",
    website: "https://sample-university.edu",
    logo: "base64encodedimage..."
  ) {
    university {
      id
      name
      description
      createdAt
    }
  }
}
```

### Create Department

```graphql
mutation {
  createDepartment(
    universityId: "university-id-here",
    name: "Computer Science",
    description: "Department of Computer Science and Engineering",
    headOfDepartment: "Prof. Jane Smith"
  ) {
    department {
      id
      name
      description
      headOfDepartment
      university {
        id
        name
      }
    }
  }
}
```

### Create Company

```graphql
mutation {
  createCompany(
    name: "Photography Studio Inc.",
    description: "Professional photography services",
    industry: "Photography",
    location: "Los Angeles",
    website: "https://photostudio.example.com",
    logo: "base64encodedimage..."
  ) {
    company {
      id
      name
      description
      industry
      createdAt
    }
  }
}
```

## Invitation System

### Send Invitation

```graphql
mutation {
  createInvitation(
    email: "invite@example.com",
    organizationId: "org-id-here",
    organizationType: UNIVERSITY,  # or COMPANY
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
```

### Accept Invitation

```graphql
mutation {
  acceptInvitation(token: "invitation-token-here") {
    success
    message
    organization {
      id
      name
    }
  }
}
```

## Post Management

### Create Post

```graphql
mutation {
  createPost(
    title: "Graduation Ceremony 2023",
    content: "Photos from this year's graduation ceremony",
    organizationId: "org-id-here",
    organizationType: UNIVERSITY,  # or COMPANY or PERSONAL
    departmentId: "department-id-here",  # optional
    images: ["base64encodedimage1...", "base64encodedimage2..."],
    tags: ["graduation", "ceremony", "2023"],
    location: "Main Campus",
    eventDate: "2023-06-15T14:00:00Z",
    privacy: PUBLIC  # or ORGANIZATION_ONLY, DEPARTMENT_ONLY, PRIVATE
  ) {
    post {
      id
      title
      content
      createdAt
      author {
        username
      }
      images {
        id
        url
      }
    }
  }
}
```

### Query Posts

```graphql
query {
  posts(
    first: 10,
    organizationId: "org-id-here",  # optional
    departmentId: "department-id-here",  # optional
    search: "graduation",  # optional
    tags: ["ceremony"],  # optional
    orderBy: "-created_at"  # sort by creation date, newest first
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
        liked  # whether the current user has liked this post
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### Home Feed

```graphql
query {
  homeFeed(first: 20) {
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
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Interaction

### Like Post

```graphql
mutation {
  likePost(postId: "post-id-here") {
    post {
      id
      likesCount
      liked
    }
  }
}
```

### Unlike Post

```graphql
mutation {
  unlikePost(postId: "post-id-here") {
    post {
      id
      likesCount
      liked
    }
  }
}
```

### Create Comment

```graphql
mutation {
  createComment(
    postId: "post-id-here",
    content: "Great photos from the event!"
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
```

### Delete Comment

```graphql
mutation {
  deleteComment(commentId: "comment-id-here") {
    success
  }
}
```

### Share Post

```graphql
mutation {
  sharePost(
    postId: "post-id-here",
    platform: "facebook"  # or "twitter", "linkedin", etc.
  ) {
    success
    shareUrl
  }
}
```

## Error Handling

GraphQL errors are returned in a consistent format:

```json
{
  "errors": [
    {
      "message": "Error description",
      "locations": [{"line": 2, "column": 3}],
      "path": ["mutation", "createPost"],
      "extensions": {
        "code": "ERROR_CODE"
      }
    }
  ]
}
```

Common error codes:
- `AUTHENTICATION_ERROR`: User is not authenticated
- `PERMISSION_DENIED`: User does not have permission for this action
- `NOT_FOUND`: Requested resource not found
- `VALIDATION_ERROR`: Input validation failed
- `ALREADY_EXISTS`: Resource already exists
- `INTERNAL_SERVER_ERROR`: Server error

## Pagination

The API uses cursor-based pagination for list queries. To paginate:

1. First request with `first` parameter:
```graphql
query {
  posts(first: 10) {
    edges {
      node { ... }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

2. Subsequent requests with `first` and `after`:
```graphql
query {
  posts(first: 10, after: "cursor-from-previous-response") {
    edges {
      node { ... }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Sample Queries

For more sample queries and mutations, check out the [GraphQL Playground Samples](graphql_playground_samples.md) document.

## Testing

For detailed testing procedures, see the [Comprehensive GraphQL Testing Guide](comprehensive_graphql_testing_guide.md). 