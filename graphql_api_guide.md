# PhotoCampus GraphQL API Guide

This guide explains how to use the GraphQL API for post management and user interactions in the PhotoCampus application.

## Getting Started

The GraphQL API is accessible at `/graphql/`. You can use the GraphiQL interface at this endpoint for testing queries and mutations.

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

### Get Current User

```graphql
{
  me {
    id
    username
    email
    firstName
    lastName
  }
}
```

## Posts API

### Queries

#### Get All Posts

```graphql
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
```

#### Get Posts with Stats (Optimized)

```graphql
{
  postsWithStats(limit: 5, offset: 0) {
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
    }
    likes {
      id
    }
    shares {
      id
    }
  }
}
```

#### Search Posts

```graphql
{
  searchPosts(searchTerm: "photo", limit: 10) {
    id
    title
    content
    author {
      username
    }
  }
}
```

### Mutations

#### Create a Post

```graphql
mutation {
  createPost(title: "My First Post", content: "This is the content of my post") {
    post {
      id
      title
      content
    }
  }
}
```

#### Update a Post

```graphql
mutation {
  updatePost(
    postId: "1", 
    title: "Updated Title", 
    content: "Updated content",
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

#### Delete a Post

```graphql
mutation {
  deletePost(postId: "1") {
    success
    message
  }
}
```

## Interactions API

### Commenting

#### Add a Comment

```graphql
mutation {
  createComment(postId: "1", content: "Great post!") {
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
```

#### Delete a Comment

```graphql
mutation {
  deleteComment(commentId: "1") {
    success
    message
  }
}
```

### Liking

#### Like a Post

```graphql
mutation {
  likePost(postId: "1") {
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
```

#### Unlike a Post

```graphql
mutation {
  unlikePost(postId: "1") {
    success
  }
}
```

### Sharing

#### Share a Post

```graphql
mutation {
  sharePost(postId: "1", sharedWith: "Twitter") {
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
```

## Advanced Querying

### Filtering Posts

```graphql
{
  allPosts(title_Contains: "photo", author_Username: "john") {
    edges {
      node {
        id
        title
        content
      }
    }
  }
}
```

### Pagination

```graphql
{
  allPosts(first: 5, after: "cursor_here") {
    edges {
      node {
        id
        title
      }
      cursor
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
```

## Error Handling

GraphQL errors are returned in the `errors` field of the response. Common errors include:

- Authentication errors (not logged in)
- Authorization errors (not permitted to perform action)
- Validation errors (invalid input)
- Not found errors (resource does not exist)

## Performance Considerations

- Use specific field selection to minimize data transfer
- Use the optimized queries (`postsWithStats`) for better performance
- Pagination is recommended for large result sets

## Testing

Use the included `test_graphql.py` script to test the API endpoints:

```bash
python test_graphql.py
``` 