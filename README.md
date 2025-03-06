# Social Media Feed Backend for University & Corporate Galleries

## Project Overview

PhotoCampus is a modern photo gallery platform designed to revolutionize how universities and companies share and preserve memories. Our primary goal is to abolish traditional paper-based yearbooks by providing a digital alternative that's more accessible, interactive, and environmentally friendly.

This backend solution focuses on creating both a scalable GraphQL API and RESTful API that supports high-volume photo collections, user interactions, and targeted content delivery. Unlike general social media platforms, PhotoCampus is specifically tailored for educational institutions and corporate environments, making it easier to find and connect with classmates, colleagues, and alumni.

## Key Features

### 📸 Digital Yearbook & Photo Management

-   Replace traditional paper yearbooks with searchable, shareable digital collections
-   Allow photo studios to showcase their professional work
-   Organize photos by universities, departments, graduating classes, and events

### 👥 User Access & Interaction

-   Public university pages accessible to all users
-   Private company/organization pages accessible via invitation only
-   Comment, like, and share functionality with social media integration
-   User-friendly compared to general social media platforms

### 🔄 Connectivity & Business Features

-   Connect with classmates and colleagues within specific institutional contexts
-   Invitation system for private corporate galleries
-   Advertisement platform for photography studios and related services
-   Analytics for user engagement and content popularity

## Technical Implementation

### Technology Stack

-   **Backend Framework**: Django
-   **Database**: PostgreSQL
-   **API Layer**: GraphQL with Graphene and REST with Django REST Framework
-   **Testing Interface**: GraphQL Playground and Swagger UI
-   **Authentication**: JWT-based authentication
-   **Caching**: Redis for enhanced performance
-   **Deployment**: Gunicorn, Nginx, and Let's Encrypt for HTTPS
-   **Monitoring**: Logging and Sentry for error tracking

### API Features

The application provides two API options:

#### GraphQL API

-   **Optimized Queries**: Efficiently load posts with related comments and likes
-   **Advanced Filtering**: Search and filter posts by multiple criteria
-   **Real-time Interactions**: Like, comment, and share functionality
-   **User Authentication**: JWT-based secure authentication
-   **Pagination**: Cursor-based pagination for efficient data loading
-   **Error Handling**: Comprehensive error handling and validation

For detailed GraphQL API documentation, see [GraphQL API Guide](graphql_api_guide.md).

#### REST API

-   **Comprehensive Endpoints**: Full CRUD operations for all resources
-   **Personalized Feed Algorithm**: Smart feed generation based on user behavior
-   **Filtering and Search**: Extensive filtering options with django-filter
-   **Rate Limiting**: Protects against abuse with different rate limits by endpoint
-   **Throttling**: Configurable throttling for high-traffic endpoints
-   **Swagger Documentation**: Interactive API documentation

### Database Schema

The database is optimized for high-volume photo storage and user interactions:

-   Users and profiles with permission levels
-   Universities and companies as organization entities
-   Photo collections with metadata and privacy settings
-   Comments, likes, and shares with efficient counter caching
-   Invitations and access control mechanisms
-   Optimized indexes for frequently queried fields
-   Constraints to maintain data integrity

## GraphQL Playground

The API includes a hosted GraphQL Playground for easy testing and exploration:

-   Interactive documentation of the entire schema
-   Real-time query composition and execution
-   Authentication testing capabilities
-   Shareable query collections for team collaboration

## Swagger UI

The REST API is fully documented with Swagger UI:

-   Interactive API documentation
-   Test endpoints directly from your browser
-   Authentication support for protected endpoints
-   Request/response examples for all endpoints

Access the Swagger UI at `http://localhost:8000/swagger/`

## Installation & Setup

### Prerequisites

-   Python 3.8+
-   PostgreSQL 12+
-   Redis (optional, for enhanced caching)

### Getting Started

1.  Clone the repository
    
    `git clone git@github.com:AbelBekele/PhotoCampus.git`
    
2.  Install dependencies

    `pip install -r requirements.txt`
    
3.  Configure environment variables
    
    `cp .env.example .env`
    
    Then edit the `.env` file with your settings
    
4.  Run migrations
    
    `python manage.py migrate`
    
5.  Create a superuser
    
    `python manage.py createsuperuser`
    
6.  Start the development server
    
    `python manage.py runserver`
    
7.  Access:
    - GraphQL Playground at `http://localhost:8000/graphql/`
    - Swagger UI at `http://localhost:8000/swagger/`
    - Admin panel at `http://localhost:8000/admin/`

## Testing

### GraphQL Testing with pytest

The project includes comprehensive pytest-based tests for the GraphQL API. These tests cover all aspects of the API, including authentication, post management, comments, likes, and shares.

#### Running GraphQL Tests

```bash
# Run all tests
pytest test_graphql.py -v

# Run specific test modules or functions
pytest test_graphql.py::test_login -v
pytest test_graphql.py::test_create_post -v

# Run tests with specific markers
pytest test_graphql.py -m "parametrize" -v
```

### REST API Testing

The REST API is tested using Django's test framework with APIClient.

#### Running REST API Tests

```bash
# Run all API tests
python manage.py test tests.test_api

# Run specific test cases
python manage.py test tests.test_api.PostAPITestCase
python manage.py test tests.test_api.CommentAPITestCase
```

## Production Deployment

For detailed deployment instructions, see our [Production Deployment Guide](deployment_guide.md).

### Key Deployment Features

-   **HTTPS**: Secure communication with Let's Encrypt certificates
-   **Database**: PostgreSQL configuration for production
-   **Caching**: Redis for high-performance caching
-   **Web Server**: Nginx serving static/media files with Gunicorn
-   **Monitoring**: Logging configuration with rotation
-   **Security**: Properly configured headers and settings

## Security Features

PhotoCampus implements multiple layers of security:

-   **Authentication**: Multiple authentication methods including JWT and session-based
-   **Authorization**: Granular permissions for different user types
-   **Data Validation**: Comprehensive input validation on all endpoints
-   **Rate Limiting**: Protection against brute force and DoS attacks
-   **HTTPS**: Enforced secure connections in production
-   **CORS**: Configurable CORS settings for production
-   **XSS Protection**: Security headers and content-type restrictions
-   **Content Security Policy**: Restricted resource loading
-   **Exception Handling**: Custom exception handlers to prevent information leakage

## Performance Optimizations

-   **Query Optimization**: Efficient database queries with select_related and prefetch_related
-   **Database Indexing**: Strategic indexing on frequently queried fields
-   **Caching**: Multi-level caching strategy with Redis
-   **Pagination**: Efficient pagination for large datasets
-   **Throttling**: Rate limiting to prevent abuse
-   **Optimized Serializers**: Customized serializers for different use cases
-   **Denormalization**: Strategic denormalization for frequently accessed data

## Development Roadmap

### Phase 1: Core Functionality ✅

-   Set up Django project with PostgreSQL
-   Create models for photos, users, and organizations
-   Implement GraphQL API with Graphene
-   Add authentication and permissions

### Phase 2: Enhanced Features ✅

-   Build invitation system for private galleries
-   Implement social media sharing
-   Create admin dashboard for universities and companies
-   Add advanced search and filtering
-   Implement REST API with DRF

### Phase 3: Scaling & Optimization ✅

-   Optimize database for high traffic
-   Implement caching strategies
-   Add analytics for user engagement
-   Develop batch upload tools for studios
-   Enhance security features

### Phase 4: Future Enhancements 🔄

-   Mobile app integration
-   AI-powered photo categorization
-   Enhanced analytics dashboard
-   Event-based notifications
-   Offline capabilities

## Why PhotoCampus?

Unlike general social media platforms, PhotoCampus creates focused communities around educational and professional contexts. Our platform makes it easier to:

-   Preserve institutional memories in a sustainable way
-   Find and connect with specific cohorts of people
-   Share professional photography in a controlled environment
-   Reduce the environmental impact of printed yearbooks

## Contact & Contribution

We welcome contributions to the PhotoCampus project! To get involved:

-   GitHub: [github.com:AbelBekele/PhotoCampus.git](https://github.com:AbelBekele/PhotoCampus.git)
-   Issue Tracker: Report bugs and feature requests through the GitHub issues page
-   Pull Requests: Submit improvements following our contribution guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details.