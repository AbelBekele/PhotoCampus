from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import University, Company, Department, OrganizationMembership, Invitation
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.models import User

# Serializers
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']
        ref_name = "OrganizationsUserSerializer"

class UniversitySerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = University
        fields = ['id', 'name', 'description', 'location', 'website', 'logo', 'logo_url', 'founded_year', 'is_private', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_logo_url(self, obj):
        """Return the absolute URL for the logo if it exists."""
        if not obj.logo:
            return None
        
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return None
    
    def validate_logo(self, value):
        if value:
            # Check file size (limit to 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image size cannot exceed 5MB")
            
            # Check file type
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not a valid image")
                
        return value
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Ensure logo URL is absolute
        if representation.get('logo') and not representation['logo'].startswith('http'):
            request = self.context.get('request')
            if request:
                representation['logo'] = request.build_absolute_uri(representation['logo'])
        
        return representation

class CompanySerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'description', 'industry', 'company_size', 'website', 'is_private', 'logo', 'logo_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_logo_url(self, obj):
        """Return the absolute URL for the logo if it exists."""
        if not obj.logo:
            return None
        
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return None
    
    def validate_logo(self, value):
        if value:
            # Check file size (limit to 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image size cannot exceed 5MB")
            
            # Check file type
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not a valid image")
                
        return value
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Ensure logo URL is absolute
        if representation.get('logo') and not representation['logo'].startswith('http'):
            request = self.context.get('request')
            if request:
                representation['logo'] = request.build_absolute_uri(representation['logo'])
        
        return representation

class DepartmentSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    university_id = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(),
        source='university',
        write_only=True
    )
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'university', 'university_id']

class OrganizationMembershipSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    university_id = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(),
        source='university',
        write_only=True,
        required=False
    )
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True,
        required=False
    )
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False
    )
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username if obj.user else None
    
    class Meta:
        model = OrganizationMembership
        fields = ['id', 'user', 'username', 'university', 'university_id', 'company', 'company_id', 
                 'department', 'department_id', 'role', 'graduation_year', 'joined_at']
        read_only_fields = ['user', 'joined_at']

class InvitationSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    inviter = UserSerializer(read_only=True)
    invitee = UserSerializer(read_only=True)
    
    class Meta:
        model = Invitation
        fields = ['id', 'token', 'email', 'inviter', 'invitee', 'university', 'company', 'department', 
                 'role', 'graduation_year', 'message', 'status', 'created_at', 'expires_at', 'responded_at']
        read_only_fields = ['token', 'created_at', 'expires_at', 'responded_at']

class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    @swagger_auto_schema(
        operation_description="Join a university",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role in the organization'),
                'department_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Department ID'),
                'graduation_year': openapi.Schema(type=openapi.TYPE_INTEGER, description='Graduation year for students')
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
        Optionally specify your role, department, and graduation year.
        """
        university = self.get_object()
        user = request.user
        
        # Check if already a member
        if OrganizationMembership.objects.filter(user=user, university=university).exists():
            return Response({'error': 'Already a member of this university'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get optional parameters
        role = request.data.get('role', 'Member')
        department_id = request.data.get('department_id')
        graduation_year = request.data.get('graduation_year')
        
        # Create membership
        membership_data = {
            'user': user,
            'university': university,
            'role': role
        }
        
        # Add department if provided
        if department_id:
            try:
                department = Department.objects.get(id=department_id, university=university)
                membership_data['department'] = department
            except Department.DoesNotExist:
                return Response({'error': 'Department not found or does not belong to this university'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        # Add graduation year if provided
        if graduation_year:
            membership_data['graduation_year'] = graduation_year
        
        membership = OrganizationMembership.objects.create(**membership_data)
        
        serializer = OrganizationMembershipSerializer(membership)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def departments(self, request, pk=None):
        """
        Get all departments for a university
        """
        university = self.get_object()
        departments = university.departments.all()
        serializer = DepartmentSerializer(departments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        Get all members of a university
        """
        university = self.get_object()
        memberships = university.memberships.select_related('user', 'department').all()
        serializer = OrganizationMembershipSerializer(memberships, many=True, context={'request': request})
        return Response(serializer.data)

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
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
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        Get all members of a company
        """
        company = self.get_object()
        memberships = company.memberships.select_related('user').all()
        serializer = OrganizationMembershipSerializer(memberships, many=True, context={'request': request})
        return Response(serializer.data)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        queryset = Department.objects.all()
        
        # Filter by university id if provided
        university_id = self.request.query_params.get('university_id', None)
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        Get all members of a department
        """
        department = self.get_object()
        memberships = department.members.select_related('user').all()
        serializer = OrganizationMembershipSerializer(memberships, many=True, context={'request': request})
        return Response(serializer.data)

class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return OrganizationMembership.objects.filter(
            user=user
        ).select_related('university', 'company', 'department')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"MembershipViewSet list method called by user {request.user}")
        logger.info(f"Serializer data type: {type(serializer.data)}")
        logger.info(f"Serializer data length: {len(serializer.data)}")
        
        # Ensure we're returning a list, even if it's empty
        # This fixes the "data.forEach is not a function" error
        response_data = serializer.data
        if not isinstance(response_data, list):
            logger.error(f"Response data is not a list: {type(response_data)}")
            # Force it to be a list
            if hasattr(response_data, 'results') and isinstance(response_data.results, list):
                response_data = response_data.results
            else:
                # Create an empty list as a last resort
                response_data = []
        
        logger.info(f"Response data (final): {response_data}")
        return Response(response_data)
    
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

class InvitationViewSet(viewsets.ModelViewSet):
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get invitations sent by this user
        return Invitation.objects.filter(
            inviter=user
        ).select_related('university', 'company', 'department')
    
    def perform_create(self, serializer):
        serializer.save(inviter=self.request.user)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Respond to an invitation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'accept': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether to accept the invitation')
            },
            required=['accept']
        ),
        responses={
            200: "Response recorded",
            400: "Invalid invitation",
            401: "Authentication required"
        }
    )
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """
        Respond to an invitation (accept or decline)
        """
        invitation = self.get_object()
        user = request.user
        accept = request.data.get('accept', False)
        
        # Check if invitation is for this user
        if invitation.email != user.email:
            return Response({'error': 'This invitation is not for your email address'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if invitation is pending
        if invitation.status != 'pending':
            return Response({'error': 'This invitation is no longer pending'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if accept:
            # Create membership
            membership = OrganizationMembership(
                user=user,
                role=invitation.role or 'Member'
            )
            
            if invitation.university:
                membership.university = invitation.university
                membership.department = invitation.department
                if invitation.graduation_year:
                    membership.graduation_year = invitation.graduation_year
                
            if invitation.company:
                membership.company = invitation.company
            
            membership.save()
            
            # Update invitation status
            invitation.status = 'accepted'
            invitation.invitee = user
            invitation.save()
            
            return Response({'success': True, 'message': 'Invitation accepted successfully'})
        else:
            # Decline invitation
            invitation.status = 'declined'
            invitation.invitee = user
            invitation.save()
            
            return Response({'success': True, 'message': 'Invitation declined'}) 