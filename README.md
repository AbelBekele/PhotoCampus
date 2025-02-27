
# Social Media Feed Backend for University & Corporate Galleries

## Project Overview

PhotoCampus is a modern photo gallery platform designed to revolutionize how universities and companies share and preserve memories. Our primary goal is to abolish traditional paper-based yearbooks by providing a digital alternative that's more accessible, interactive, and environmentally friendly.

This backend solution focuses on creating a scalable GraphQL API that supports high-volume photo collections, user interactions, and targeted content delivery. Unlike general social media platforms, PhotoCampus is specifically tailored for educational institutions and corporate environments, making it easier to find and connect with classmates, colleagues, and alumni.

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
-   **API Layer**: GraphQL with Graphene
-   **Testing Interface**: GraphQL Playground
-   **Authentication**: JWT-based authentication

### Database Schema

The database is optimized for high-volume photo storage and user interactions:

-   Users and profiles with permission levels
-   Universities and companies as organization entities
-   Photo collections with metadata and privacy settings
-   Comments, likes, and shares with efficient counter caching
-   Invitations and access control mechanisms

### GraphQL Implementation

Our GraphQL API enables:

-   Flexible querying of photos with filter options
-   Complex data fetching in a single request
-   Real-time updates for user interactions
-   Schema-defined API that's self-documenting


## GraphQL Playground

The API includes a hosted GraphQL Playground for easy testing and exploration:

-   Interactive documentation of the entire schema
-   Real-time query composition and execution
-   Authentication testing capabilities
-   Shareable query collections for team collaboration

## Installation & Setup

### Prerequisites

-   Python 3.8+
-   PostgreSQL
-   pipenv or venv

### Getting Started

1.  Clone the repository
    
    `git clone git@github.com:AbelBekele/PhotoCampus.git`
    
2.  Install dependencies

    `pip install -r requirements.txt`
    
3.  Configure database settings in `settings.py`
5.  Run migrations
    
    `python manage.py migrate`
    
6.  Start the development server
    
    `python manage.py runserver`
    
7.  Access GraphQL Playground at `http://localhost:8000/graphql/`

## Performance Optimizations

-   Database query optimization for high-volume photo collections
-   Efficient counter caching for interaction metrics
-   Pagination strategies for large result sets
-   Strategic indexing on frequently queried fields
-   Denormalization where appropriate for performance

## Development Roadmap

### Phase 1: Core Functionality

-   Set up Django project with PostgreSQL
-   Create models for photos, users, and organizations
-   Implement GraphQL API with Graphene
-   Add authentication and permissions

### Phase 2: Enhanced Features

-   Build invitation system for private galleries
-   Implement social media sharing
-   Create admin dashboard for universities and companies
-   Add advanced search and filtering

### Phase 3: Scaling & Optimization

-   Optimize database for high traffic
-   Implement caching strategies
-   Add analytics for user engagement
-   Develop batch upload tools for studios

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