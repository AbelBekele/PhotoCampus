from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import UniversityViewSet, CompanyViewSet, DepartmentViewSet, MembershipViewSet, InvitationViewSet

router = DefaultRouter()
router.register(r'universities', UniversityViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'memberships', MembershipViewSet, basename='membership')
router.register(r'invitations', InvitationViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),
] 