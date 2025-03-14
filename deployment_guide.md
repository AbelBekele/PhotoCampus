# PhotoCampus Production Deployment Guide

This guide provides comprehensive instructions for deploying the PhotoCampus application to a production environment. Following these steps will ensure your deployment is secure, performant, and reliable.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Static & Media Files](#static-and-media-files)
5. [Web Server Configuration](#web-server-configuration)
6. [Security Settings](#security-settings)
7. [Caching Setup](#caching-setup)
8. [Monitoring & Logging](#monitoring-and-logging)
9. [Deployment Checklist](#deployment-checklist)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin deployment, ensure you have:

- A server running Linux (Ubuntu 22.04+ recommended)
- Python 3.10+ installed
- PostgreSQL 14+ installed
- Redis server for caching and Celery
- Domain name configured with DNS (for HTTPS)
- SSH access to your server

## Environment Setup

1. **Create a dedicated user**:
   ```bash
   sudo adduser photocampus
   sudo usermod -aG sudo photocampus
   ```

2. **Clone the repository**:
   ```bash
   sudo apt update
   sudo apt install git
   git clone https://github.com/AbelBekele/PhotoCampus.git
   cd PhotoCampus
   ```

3. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file based on the `.env.example`:
   ```bash
   cp .env.example .env
   ```
   
   Then edit the `.env` file with your production settings:
   ```
   DEBUG=False
   SECRET_KEY=your_secure_random_key_here
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   
   # Database settings
   DB_NAME=photocampus
   DB_USER=db_username
   DB_PASSWORD=secure_db_password
   DB_HOST=localhost
   DB_PORT=5432
   
   # Email settings
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@example.com
   EMAIL_HOST_PASSWORD=your_email_password
   EMAIL_USE_TLS=True
   
   # CORS settings
   CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   
   # Redis settings
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/1
   CELERY_RESULT_BACKEND=redis://localhost:6379/2
   ```

## Database Configuration

1. **Create PostgreSQL database**:
   ```bash
   sudo -u postgres psql
   
   CREATE DATABASE photocampus;
   CREATE USER db_username WITH PASSWORD 'secure_db_password';
   ALTER ROLE db_username SET client_encoding TO 'utf8';
   ALTER ROLE db_username SET default_transaction_isolation TO 'read committed';
   ALTER ROLE db_username SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE photocampus TO db_username;
   \q
   ```

2. **Set up the database in Django**:
   The PostgreSQL configuration should already be in place in the settings file. Ensure it matches your environment variables:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': config('DB_NAME'),
           'USER': config('DB_USER'),
           'PASSWORD': config('DB_PASSWORD'),
           'HOST': config('DB_HOST'),
           'PORT': config('DB_PORT'),
           'CONN_MAX_AGE': 60,  # Keep connections alive for 60 seconds
       }
   }
   ```

3. **Apply migrations and create a superuser**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Static and Media Files

1. **Configure static files**:
   Ensure your settings have:
   ```python
   STATIC_URL = '/static/'
   STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
   STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
   ```

2. **Configure media files**:
   ```python
   MEDIA_URL = '/media/'
   MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
   ```

3. **Collect static files**:
   ```bash
   python manage.py collectstatic
   ```

4. **Create necessary directories**:
   ```bash
   mkdir -p media/posts
   mkdir -p media/organizations/logos
   chmod -R 755 media
   ```

## Web Server Configuration

### Using Gunicorn and Nginx

1. **Install Gunicorn**:
   ```bash
   pip install gunicorn
   ```

2. **Create a Gunicorn systemd service**:
   Create `/etc/systemd/system/photocampus.service`:
   ```
   [Unit]
   Description=PhotoCampus Gunicorn daemon
   After=network.target

   [Service]
   User=photocampus
   Group=www-data
   WorkingDirectory=/home/photocampus/PhotoCampus
   ExecStart=/home/photocampus/PhotoCampus/venv/bin/gunicorn \
             --access-logfile - \
             --workers 3 \
             --bind unix:/home/photocampus/PhotoCampus/photocampus.sock \
             photocampus.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

3. **Create Celery worker and beat services**:
   Create `/etc/systemd/system/photocampus-celery.service`:
   ```
   [Unit]
   Description=PhotoCampus Celery Worker
   After=network.target

   [Service]
   User=photocampus
   Group=www-data
   WorkingDirectory=/home/photocampus/PhotoCampus
   ExecStart=/home/photocampus/PhotoCampus/venv/bin/celery -A photocampus worker -l info

   [Install]
   WantedBy=multi-user.target
   ```
   
   Create `/etc/systemd/system/photocampus-celerybeat.service`:
   ```
   [Unit]
   Description=PhotoCampus Celery Beat
   After=network.target

   [Service]
   User=photocampus
   Group=www-data
   WorkingDirectory=/home/photocampus/PhotoCampus
   ExecStart=/home/photocampus/PhotoCampus/venv/bin/celery -A photocampus beat -l info

   [Install]
   WantedBy=multi-user.target
   ```

4. **Install and configure Nginx**:
   ```bash
   sudo apt install nginx
   ```
   
   Create `/etc/nginx/sites-available/photocampus`:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       
       location = /favicon.ico { access_log off; log_not_found off; }
       
       location /static/ {
           root /home/photocampus/PhotoCampus;
       }
       
       location /media/ {
           root /home/photocampus/PhotoCampus;
       }
       
       location / {
           include proxy_params;
           proxy_pass http://unix:/home/photocampus/PhotoCampus/photocampus.sock;
       }
   }
   ```

5. **Enable the site and start services**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/photocampus /etc/nginx/sites-enabled
   sudo systemctl daemon-reload
   sudo systemctl start photocampus
   sudo systemctl enable photocampus
   sudo systemctl start photocampus-celery
   sudo systemctl enable photocampus-celery
   sudo systemctl start photocampus-celerybeat
   sudo systemctl enable photocampus-celerybeat
   sudo systemctl restart nginx
   ```

6. **Set up HTTPS with Let's Encrypt**:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

## Security Settings

1. **Ensure these settings are enabled in production**:
   ```python
   DEBUG = False
   SECRET_KEY = config('SECRET_KEY')
   ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])
   
   # Security headers
   SECURE_CONTENT_TYPE_NOSNIFF = True
   SECURE_BROWSER_XSS_FILTER = True
   X_FRAME_OPTIONS = 'DENY'
   
   # HTTPS settings (with Nginx/Let's Encrypt)
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_HSTS_SECONDS = 31536000  # 1 year
   SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   SECURE_HSTS_PRELOAD = True
   ```

2. **Set up firewall**:
   ```bash
   sudo ufw allow 'Nginx Full'
   sudo ufw allow OpenSSH
   sudo ufw enable
   ```

## Caching Setup

1. **Install Redis**:
   ```bash
   sudo apt install redis-server
   sudo systemctl enable redis-server
   ```

2. **Configure Redis in Django**:
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/0'),
           'OPTIONS': {
               'CLIENT_CLASS': 'django_redis.client.DefaultClient',
           }
       }
   }
   
   # Use Redis as session backend
   SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
   SESSION_CACHE_ALIAS = 'default'
   
   # Celery settings
   CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/1')
   CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/2')
   ```

## Monitoring and Logging

1. **Configure Django logging**:
   ```python
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'verbose': {
               'format': '{levelname} {asctime} {module} {message}',
               'style': '{',
           },
       },
       'handlers': {
           'file': {
               'level': 'WARNING',
               'class': 'logging.FileHandler',
               'filename': '/var/log/photocampus/django.log',
               'formatter': 'verbose',
           },
       },
       'loggers': {
           'django': {
               'handlers': ['file'],
               'level': 'WARNING',
               'propagate': True,
           },
       },
   }
   ```

2. **Create log directory**:
   ```bash
   sudo mkdir -p /var/log/photocampus
   sudo chown -R photocampus:www-data /var/log/photocampus
   ```

3. **Setup Sentry (optional but recommended)**:
   ```bash
   pip install sentry-sdk
   ```
   
   Add to settings.py:
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.django import DjangoIntegration
   
   sentry_sdk.init(
       dsn=config('SENTRY_DSN', default=''),
       integrations=[DjangoIntegration()],
       traces_sample_rate=0.5,
       send_default_pii=True
   )
   ```

## Deployment Checklist

Before going live, verify these final items:

1. **Run Django deployment check**:
   ```bash
   python manage.py check --deploy
   ```

2. **Test site functionality**:
   - User registration and login
   - Post creation and editing
   - Image uploads
   - Comment functionality
   - Like and share mechanisms
   - Organization features
   - Invitation system
   - GraphQL API endpoints
   - RESTful API endpoints

3. **Performance testing**:
   - Database query optimization
   - Page load times
   - API response times
   - Caching effectiveness

4. **Setup regular backups**:
   ```bash
   # Example backup script for postgres
   pg_dump -U db_username photocampus > /path/to/backups/photocampus_$(date +%Y-%m-%d).sql
   
   # Media file backups
   rsync -av /home/photocampus/PhotoCampus/media/ /path/to/backups/media/
   ```

5. **Setup monitoring**:
   Consider implementing:
   - Server monitoring with Prometheus/Grafana
   - Error tracking with Sentry
   - Redis monitoring for cache performance

## Troubleshooting

Common issues and their solutions:

1. **Static files not loading**:
   - Check Nginx configuration
   - Verify `collectstatic` was run
   - Check file permissions

2. **Database connection issues**:
   - Verify PostgreSQL is running: `sudo systemctl status postgresql`
   - Check database credentials in `.env`
   - Ensure database user has proper permissions

3. **500 errors**:
   - Check Gunicorn logs: `sudo journalctl -u photocampus`
   - Check Django logs: `/var/log/photocampus/django.log`
   - Verify all dependencies are installed correctly

4. **Media upload issues**:
   - Check directory permissions
   - Verify Nginx configuration for media files
   - Check disk space: `df -h`

5. **Celery task issues**:
   - Check Celery logs: `sudo journalctl -u photocampus-celery`
   - Verify Redis is running: `sudo systemctl status redis-server`
   - Test Celery manually: `celery -A photocampus worker --loglevel=debug`

For additional support, refer to Django's documentation or open an issue in the project repository. 