from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
from django_redis import get_redis_connection as django_get_redis_connection
from django.conf import settings
import redis

logger = logging.getLogger(__name__)

def get_redis_connection(alias="default"):
    """
    Wrapper around django_redis.get_redis_connection that ensures
    consistent database usage across the application.
    
    This function should ONLY be used for caching purposes, not for
    storing application data. Application data should be stored in
    the primary database (PostgreSQL/SQLite).
    """
    try:
        # Get the connection using django-redis, which is configured
        # for caching in settings.py
        return django_get_redis_connection(alias)
    except Exception as e:
        logger.error(f"Redis connection error with alias '{alias}': {str(e)}")
        logger.warning("Redis should only be used for caching, not for application data storage.")
        
        # If the connection fails, log the error and raise an exception
        # to prevent silent failures
        raise RuntimeError(f"Redis connection failed: {str(e)}")

def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework that improves error responses.
    
    Returns standardized error responses with appropriate status codes and
    detailed error messages where appropriate.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, it means DRF can't handle this exception
    if response is None:
        # Log unhandled exceptions for debugging
        logger.error(f"Unhandled exception: {exc}")
        
        if hasattr(exc, 'message'):
            error_message = exc.message
        else:
            error_message = str(exc)
            
        return Response(
            {"error": "Server error", "detail": error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    # Add more context to authentication errors
    if response.status_code == 401:
        response.data = {
            "error": "Authentication failed",
            "detail": response.data.get("detail", "Authentication credentials were not provided or are invalid."),
            "status_code": response.status_code
        }
        
    # Add more context to permission errors
    elif response.status_code == 403:
        response.data = {
            "error": "Permission denied",
            "detail": response.data.get("detail", "You do not have permission to perform this action."),
            "status_code": response.status_code
        }
        
    # Enhance validation error responses
    elif response.status_code == 400:
        response.data = {
            "error": "Bad request",
            "detail": response.data,
            "status_code": response.status_code
        }
        
    # Enhance not found responses
    elif response.status_code == 404:
        response.data = {
            "error": "Not found",
            "detail": response.data.get("detail", "The requested resource was not found."),
            "status_code": response.status_code
        }
    
    # Add status code to all responses for consistency
    elif isinstance(response.data, dict):
        response.data['status_code'] = response.status_code
        
    return response 