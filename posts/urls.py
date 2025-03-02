from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import PostViewSet, CommentViewSet, LikeViewSet, ShareViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'likes', LikeViewSet)
router.register(r'shares', ShareViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
] 