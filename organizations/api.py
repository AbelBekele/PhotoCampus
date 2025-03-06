from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import University, Company, Department, OrganizationMembership
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Serializers
from rest_framework import serializers

class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'description', 'location', 'website', 'logo']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'description', 'industry', 'location', 'website', 'logo']

class DepartmentSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'university']

class OrganizationMembershipSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    
    class Meta:
        model = OrganizationMembership
        fields = ['id', 'user', 'university', 'company', 'role', 'joined_at']
        read_only_fields = ['user', 'joined_at']

class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Join a university",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role in the organization')
            }
        ),
        responses={
            200: OrganizationMembershipSerializer(),
            400: "Already a member",
            401: "Authentication required"
        }
    )
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Join a university as a member.
        Optionally specify your role.
        """
        university = self.get_object()
        user = request.user
        
        # Check if already a member
        if OrganizationMembership.objects.filter(user=user, university=university).exists():
            return Response({'error': 'Already a member of this university'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create membership
        role = request.data.get('role', 'Member')
        membership = OrganizationMembership.objects.create(
            user=user,
            university=university,
            role=role
        )
        
        serializer = OrganizationMembershipSerializer(membership)
        return Response(serializer.data)

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Join a company",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role in the organization')
            }
        ),
        responses={
            200: OrganizationMembershipSerializer(),
            400: "Already a member",
            401: "Authentication required"
        }
    )
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Join a company as a member.
        Optionally specify your role.
        """
        company = self.get_object()
        user = request.user
        
        # Check if already a member
        if OrganizationMembership.objects.filter(user=user, company=company).exists():
            return Response({'error': 'Already a member of this company'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create membership
        role = request.data.get('role', 'Member')
        membership = OrganizationMembership.objects.create(
            user=user,
            company=company,
            role=role
        )
        
        serializer = OrganizationMembershipSerializer(membership)
        return Response(serializer.data)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user
        ).select_related('university', 'company')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=False, methods=['get'])
    def explore(self, request):
        """
        Returns organizations the user is not a member of
        """
        user = request.user
        
        # Get user's current memberships
        university_memberships = OrganizationMembership.objects.filter(
            user=user, university__isnull=False
        ).values_list('university_id', flat=True)
        
        company_memberships = OrganizationMembership.objects.filter(
            user=user, company__isnull=False
        ).values_list('company_id', flat=True)
        
        # Get universities and companies user is not a member of
        universities = University.objects.exclude(id__in=university_memberships)[:5]
        companies = Company.objects.exclude(id__in=company_memberships)[:5]
        
        # Serialize
        university_serializer = UniversitySerializer(universities, many=True)
        company_serializer = CompanySerializer(companies, many=True)
        
        return Response({
            'universities': university_serializer.data,
            'companies': company_serializer.data
        }) 