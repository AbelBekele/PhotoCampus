"""
URL configuration for photocampus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.contrib.auth import views as auth_views
from . import views

# Import for Swagger documentation
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import the viewsets
from posts.api import PostViewSet, CommentViewSet, LikeViewSet, ShareViewSet
from organizations.api import UniversityViewSet, CompanyViewSet, DepartmentViewSet, MembershipViewSet
from rest_framework.routers import DefaultRouter

# Create API routers
router = DefaultRouter()

# Register posts endpoints
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'likes', LikeViewSet)
router.register(r'shares', ShareViewSet)

# Register organizations endpoints
router.register(r'organizations/universities', UniversityViewSet)
router.register(r'organizations/companies', CompanyViewSet)
router.register(r'organizations/departments', DepartmentViewSet)
router.register(r'organizations/memberships', MembershipViewSet, basename='membership')

schema_view = get_schema_view(
    openapi.Info(
        title="PhotoCampus API",
        default_version='v1',
        description="API documentation for PhotoCampus application",
        terms_of_service="https://www.photocampus.com/terms/",
        contact=openapi.Contact(email="contact@photocampus.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    url='https://photocampus.abelbekele.com',
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    
    # Authentication URLs
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt',
        success_url='/accounts/password_reset/done/'
    ), name='password_reset'),
    path('accounts/password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('accounts/reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
         name='password_reset_complete'),
    
    # REST API endpoints
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    
    # Swagger documentation URLs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Templates
    path('', login_required(TemplateView.as_view(template_name='home_feed.html')), name='home'),
    path('organizations/explore/', login_required(TemplateView.as_view(template_name='explore_organizations.html')), name='explore_organizations'),
    
    # Include organizations URLs
    path('organizations/', include('organizations.urls')),
    
    # Post detail view
    path('posts/<int:id>/', login_required(TemplateView.as_view(template_name='post_detail.html')), name='post_detail'),
    
    # Invitation handling
    path('invitation/<uuid:token>/', views.invitation_view, name='invitation'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, Django shouldn't serve media files itself.
    # This is just a placeholder to avoid URL pattern errors in non-debug environment
    # In production, your web server (Nginx, Apache, etc.) should handle media files
    # or you could use a CDN for better performance
    urlpatterns += [
        path('media/<path:path>', lambda request, path: HttpResponseNotFound(), name='media'),
    ]
