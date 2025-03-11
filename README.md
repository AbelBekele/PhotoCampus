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

### 📧 Invitation System

- Email-based invitation system for organization administrators to invite members
- Customized HTML email templates for different organization types
- Token-based secure invitation acceptance process
- Invitation management with status tracking (pending, accepted, declined, expired)
- Automated retry mechanism for failed email deliveries
- Scheduled processing of pending invitations via Celery tasks

### 🏠 Personalized Home Feed

- Intelligent content curation algorithm tailored to user preferences
- Prioritizes content from the user's organizations, departments, and connections
- Smart categorization of trending posts and recent activities
- For detailed explanation of the algorithm, see [Home Feed Explained](home_feed_explained.md)

## Technical Implementation

### Technology Stack

-   **Backend Framework**: Django 5.0
-   **Database**: PostgreSQL
-   **API Layer**: GraphQL with Graphene and REST with Django REST Framework
-   **Testing Interface**: GraphQL Playground and Swagger UI
-   **Authentication**: JWT-based authentication
-   **Caching**: Redis for enhanced performance
-   **Task Queue**: Celery for background processing and scheduled tasks
-   **Email**: SMTP with HTML template support
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

For a visual representation of the database schema, see the ERD diagrams in the `erd_diagrams/` directory.

## API Documentation & Testing Tools

### GraphQL Playground

The API includes a hosted GraphQL Playground for easy testing and exploration:

-   Interactive documentation of the entire schema
-   Real-time query composition and execution
-   Authentication testing capabilities
-   Shareable query collections for team collaboration

### Swagger UI

The REST API is fully documented with Swagger UI:

-   Interactive API documentation
-   Test endpoints directly from your browser
-   Authentication support for protected endpoints
-   Request/response examples for all endpoints

### ReDoc

An alternative REST API documentation interface with a clean, responsive design:
- Comprehensive endpoint documentation
- Request/response schemas
- Syntax-highlighted examples

## Installation & Setup

### Prerequisites

-   Python 3.10+
-   PostgreSQL 14+
-   Redis (for caching and Celery tasks)

### Getting Started

1.  Clone the repository
    
    `git clone https://github.com/AbelBekele/PhotoCampus.git`
    
2.  Install dependencies

    `pip install -r requirements.txt`
    
3.  Configure environment variables
    
    `cp .env.example .env`
    
    Then edit the `.env` file with your settings, including SMTP credentials for email functionality
    
4.  Run migrations
    
    `python manage.py migrate`
    
5.  Create a superuser
    
    `python manage.py createsuperuser`
    
6.  Start the development server
    
    `python manage.py runserver`
    
7.  Start Celery worker for background tasks (in a separate terminal)
    
    `celery -A photocampus worker -l info`
    
8.  Start Celery beat for scheduled tasks (in a separate terminal)
    
    `celery -A photocampus beat -l info`
    
9.  Access:
    - Main application: `https://photocampus.abelbekele.com/`
    - Login page: `https://photocampus.abelbekele.com/login/`
    - Home feed: `https://photocampus.abelbekele.com/home/`
    - GraphQL Playground: `https://photocampus.abelbekele.com/graphql/`
    - Swagger UI: `https://photocampus.abelbekele.com/swagger/`
    - ReDoc: `https://photocampus.abelbekele.com/redoc/`
    - Admin panel: `https://photocampus.abelbekele.com/admin/`

## Testing

### GraphQL Testing with pytest

The project includes comprehensive pytest-based tests for the GraphQL API. These tests cover all aspects of the API, including authentication, post management, comments, likes, and shares.

For detailed testing guidance, see our [Comprehensive GraphQL Testing Guide](comprehensive_graphql_testing_guide.md).

#### Running GraphQL Tests

```bash
# Run all tests
pytest tests/test_graphql.py -v

# Run specific test modules or functions
pytest tests/test_graphql.py::test_login -v
pytest tests/test_graphql.py::test_create_post -v

# Run tests with specific markers
pytest -m "graphql" -v
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
-   **Email Security**: Secure token-based invitation system

## Performance Optimizations

-   **Query Optimization**: Efficient database queries with select_related and prefetch_related
-   **Database Indexing**: Strategic indexing on frequently queried fields
-   **Caching**: Multi-level caching strategy with Redis
-   **Pagination**: Efficient pagination for large datasets
-   **Throttling**: Rate limiting to prevent abuse
-   **Optimized Serializers**: Customized serializers for different use cases
-   **Denormalization**: Strategic denormalization for frequently accessed data
-   **Background Processing**: Celery for handling resource-intensive tasks

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
-   Add email notification system with HTML templates

### Phase 4: Future Enhancements 🚀

-   Mobile app integration
-   AI-powered photo categorization
-   Enhanced analytics dashboard
-   Event-based notifications
-   Offline capabilities
-   Real-time feed updates with WebSockets

## Why PhotoCampus?

Unlike general social media platforms, PhotoCampus creates focused communities around educational and professional contexts. Our platform makes it easier to:

-   Preserve institutional memories in a sustainable way
-   Connect with specific educational or professional communities
-   Find and reconnect with alumni and former colleagues
-   Create a sense of belonging to organizations
-   Maintain professional networks in a photo-centric environment

## Contributing

We welcome contributions to the PhotoCampus project! Please follow standard GitHub flow:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Contact

For questions, support, or inquiries about PhotoCampus, please contact:

- Email: support@photocampus.com
- GitHub: [https://github.com/AbelBekele/PhotoCampus](https://github.com/AbelBekele/PhotoCampus)