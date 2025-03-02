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

# Get current authenticated user
query Me {
  me {
    id
    username
    email
    firstName
    lastName
  }
}
```

## Posts

```graphql
# Query all posts (paginated)
query AllPosts {
  allPosts(first: 5) {
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
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# Get optimized posts with stats
query PostsWithStats {
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
    }
  }
}

# Search posts
query SearchPosts {
  searchPosts(searchTerm: "photo", limit: 5) {
    id
    title
    content
    author {
      username
    }
  }
}

# Create a new post
mutation CreatePost {
  createPost(
    title: "My First GraphQL Post"
    content: "This post was created using GraphQL!"
  ) {
    post {
      id
      title
      content
      createdAt
    }
  }
}

# Update a post
mutation UpdatePost {
  updatePost(
    postId: "1"
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

# Delete a post
mutation DeletePost {
  deletePost(postId: "1") {
    success
    message
  }
}
```

## Interactions

```graphql
# Add a comment
mutation AddComment {
  createComment(
    postId: "1"
    content: "This is a great post! Thanks for sharing."
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

# Delete a comment
mutation DeleteComment {
  deleteComment(commentId: "1") {
    success
    message
  }
}

# Like a post
mutation LikePost {
  likePost(postId: "1") {
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

# Unlike a post
mutation UnlikePost {
  unlikePost(postId: "1") {
    success
  }
}

# Share a post
mutation SharePost {
  sharePost(
    postId: "1"
    sharedWith: "LinkedIn"
  ) {
    share {
      id
      sharedWith
      createdAt
      user {
        username
      }
    }
  }
}
```

## Advanced Filtering

```graphql
# Filter posts by title and author
query FilteredPosts {
  allPosts(title_Contains: "graduation", author_Username: "john") {
    edges {
      node {
        id
        title
        content
        author {
          username
        }
      }
    }
  }
}

# Posts created in a date range
query DateFilteredPosts {
  allPosts(created_After: "2023-01-01", created_Before: "2023-12-31") {
    edges {
      node {
        id
        title
        createdAt
      }
    }
  }
}
```

## Tips for Using GraphQL Playground

1. **Authentication**: After getting a token, add it to the HTTP Headers panel at the bottom:
   ```json
   {
     "Authorization": "JWT your_token_here"
   }
   ```

2. **Variables**: For queries with variables, use the Query Variables panel:
   ```json
   {
     "postId": "1",
     "content": "This is a comment with variables"
   }
   ```

3. **Documentation**: Use the Documentation Explorer (right sidebar) to explore the schema and available operations. 