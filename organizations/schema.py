import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth.models import User
from .models import University, Company, Department, OrganizationMembership, Invitation
import django_filters
from graphene import relay
from django.contrib.auth import get_user_model

# Define Types
class UniversityType(DjangoObjectType):
    class Meta:
        model = University
        fields = '__all__'
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'location': ['exact', 'icontains'],
            'is_private': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class CompanyType(DjangoObjectType):
    class Meta:
        model = Company
        fields = '__all__'
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'industry': ['exact', 'icontains'],
            'is_private': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class DepartmentType(DjangoObjectType):
    class Meta:
        model = Department
        fields = '__all__'
        filter_fields = {
            'name': ['exact', 'icontains'],
            'university__name': ['exact', 'icontains'],
        }
        interfaces = (graphene.relay.Node,)

class OrganizationMembershipType(DjangoObjectType):
    class Meta:
        model = OrganizationMembership
        fields = '__all__'
        filter_fields = {
            'role': ['exact', 'icontains'],
            'university__name': ['exact'],
            'company__name': ['exact'],
            'department__name': ['exact'],
            'user__username': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class InvitationType(DjangoObjectType):
    class Meta:
        model = Invitation
        fields = '__all__'
        filter_fields = {
            'status': ['exact'],
            'email': ['exact', 'icontains'],
            'university__name': ['exact'],
            'company__name': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

# Query
class Query(graphene.ObjectType):
    # Single item queries
    university = graphene.relay.Node.Field(UniversityType)
    company = graphene.relay.Node.Field(CompanyType)
    department = graphene.relay.Node.Field(DepartmentType)
    membership = graphene.relay.Node.Field(OrganizationMembershipType)
    invitation = graphene.relay.Node.Field(InvitationType)
    
    # List queries
    all_universities = DjangoFilterConnectionField(UniversityType)
    all_companies = DjangoFilterConnectionField(CompanyType)
    all_departments = DjangoFilterConnectionField(DepartmentType)
    
    # For authenticated users
    my_memberships = DjangoFilterConnectionField(OrganizationMembershipType)
    my_invitations = DjangoFilterConnectionField(InvitationType)
    
    # For organization admins
    organization_members = DjangoFilterConnectionField(OrganizationMembershipType)
    organization_invitations = DjangoFilterConnectionField(InvitationType)
    
    def resolve_all_universities(self, info, **kwargs):
        # Only return public universities unless user is authenticated
        if info.context.user.is_authenticated:
            return University.objects.all()
        return University.objects.filter(is_private=False)
    
    def resolve_all_companies(self, info, **kwargs):
        # Only return public companies unless user is authenticated
        if info.context.user.is_authenticated:
            return Company.objects.all()
        return Company.objects.filter(is_private=False)
    
    def resolve_all_departments(self, info, **kwargs):
        return Department.objects.all()
    
    def resolve_my_memberships(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("You must be logged in to view your memberships")
        return OrganizationMembership.objects.filter(user=user)
    
    def resolve_my_invitations(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("You must be logged in to view your invitations")
        return Invitation.objects.filter(
            email=user.email, 
            status='pending'
        )
    
    def resolve_organization_members(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        # Get all orgs where user is admin
        admin_universities = user.administered_universities.all()
        admin_companies = user.administered_companies.all()
        
        # Return members of those orgs
        memberships = OrganizationMembership.objects.none()
        if admin_universities.exists():
            memberships = memberships | OrganizationMembership.objects.filter(
                university__in=admin_universities
            )
        if admin_companies.exists():
            memberships = memberships | OrganizationMembership.objects.filter(
                company__in=admin_companies
            )
        
        return memberships
    
    def resolve_organization_invitations(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        # Get all orgs where user is admin
        admin_universities = user.administered_universities.all()
        admin_companies = user.administered_companies.all()
        
        # Return invitations for those orgs
        invitations = Invitation.objects.none()
        if admin_universities.exists():
            invitations = invitations | Invitation.objects.filter(
                university__in=admin_universities
            )
        if admin_companies.exists():
            invitations = invitations | Invitation.objects.filter(
                company__in=admin_companies
            )
        
        return invitations

# Mutations
class CreateUniversity(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        location = graphene.String(required=False)
        founded_year = graphene.Int(required=False)
        website = graphene.String(required=False)
        is_private = graphene.Boolean(required=False, default_value=False)

    university = graphene.Field(UniversityType)

    def mutate(self, info, name, description=None, location=None, founded_year=None, 
              website=None, is_private=False):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("You must be logged in to create a university")
        
        university = University(
            name=name,
            description=description or "",
            location=location or "",
            founded_year=founded_year,
            website=website or "",
            is_private=is_private
        )
        university.save()
        
        # Make the creator an admin
        university.admins.add(user)
        
        return CreateUniversity(university=university)

class CreateCompany(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        industry = graphene.String(required=False)
        company_size = graphene.String(required=False)
        website = graphene.String(required=False)
        is_private = graphene.Boolean(required=False, default_value=False)

    company = graphene.Field(CompanyType)

    def mutate(self, info, name, description=None, industry=None, company_size=None, 
              website=None, is_private=False):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("You must be logged in to create a company")
        
        company = Company(
            name=name,
            description=description or "",
            industry=industry or "",
            company_size=company_size or "",
            website=website or "",
            is_private=is_private
        )
        company.save()
        
        # Make the creator an admin
        company.admins.add(user)
        
        return CreateCompany(company=company)

class CreateDepartment(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        university_id = graphene.ID(required=True)
        description = graphene.String(required=False)

    department = graphene.Field(DepartmentType)

    def mutate(self, info, name, university_id, description=None):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("You must be logged in to create a department")
        
        # Get the university
        university = University.objects.get(pk=university_id)
        
        # Check if user is admin of the university
        if not university.admins.filter(id=user.id).exists():
            raise Exception("You must be an admin of the university to create departments")
        
        department = Department(
            name=name,
            university=university,
            description=description or ""
        )
        department.save()
        
        return CreateDepartment(department=department)

class CreateInvitation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        university_id = graphene.ID(required=False)
        company_id = graphene.ID(required=False)
        department_id = graphene.ID(required=False)
        role = graphene.String(required=False)
        message = graphene.String(required=False)
        first_name = graphene.String(required=False)

    invitation = graphene.Field(InvitationType)

    def mutate(self, info, email, university_id=None, company_id=None, 
              department_id=None, role=None, message=None, first_name=None):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("You must be logged in to send invitations")
        
        if not (university_id or company_id):
            raise Exception("You must specify either a university or company")
        
        if university_id and company_id:
            raise Exception("You can only invite to one organization at a time")
        
        invitation = Invitation(
            email=email,
            inviter=user,
            role=role or "",
            message=message or ""
        )
        
        organization_name = ""
        organization_type = ""
        
        if university_id:
            university = University.objects.get(pk=university_id)
            # Check if user is admin
            if not university.admins.filter(id=user.id).exists():
                raise Exception("You must be an admin of the university to send invitations")
            invitation.university = university
            organization_name = university.name
            organization_type = "university"
            
            if department_id:
                department = Department.objects.get(pk=department_id)
                if department.university.id != university.id:
                    raise Exception("Department must belong to the selected university")
                invitation.department = department
        
        if company_id:
            company = Company.objects.get(pk=company_id)
            # Check if user is admin
            if not company.admins.filter(id=user.id).exists():
                raise Exception("You must be an admin of the company to send invitations")
            invitation.company = company
            organization_name = company.name
            organization_type = "company"
        
        invitation.save()
        
        # Send invitation email
        from organizations.tasks import send_organization_invitation_email
        
        # If first_name not provided, use a default
        if not first_name:
            first_name = "there"  # Generic greeting if name not available
            
        # Send email asynchronously using Celery
        send_organization_invitation_email.delay(
            invitation_id=invitation.id,
            email=email,
            first_name=first_name,
            organization_name=organization_name,
            organization_type=organization_type,
            invitation_token=str(invitation.token)
        )
        
        return CreateInvitation(invitation=invitation)

class RespondToInvitation(graphene.Mutation):
    class Arguments:
        invitation_token = graphene.String(required=True)
        accept = graphene.Boolean(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, invitation_token, accept):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("You must be logged in to respond to invitations")
        
        try:
            invitation = Invitation.objects.get(token=invitation_token, status='pending')
            
            # Check if the invitation is for this user
            if invitation.email != user.email:
                return RespondToInvitation(
                    success=False,
                    message="This invitation is not for your email address"
                )
            
            if accept:
                # Create membership
                membership = OrganizationMembership(
                    user=user,
                    role=invitation.role
                )
                
                if invitation.university:
                    membership.university = invitation.university
                    membership.department = invitation.department
                    
                if invitation.company:
                    membership.company = invitation.company
                
                membership.save()
                
                # Update invitation status
                invitation.status = 'accepted'
                invitation.invitee = user
                invitation.save()
                
                return RespondToInvitation(
                    success=True,
                    message="Invitation accepted successfully"
                )
            else:
                # Decline invitation
                invitation.status = 'declined'
                invitation.invitee = user
                invitation.save()
                
                return RespondToInvitation(
                    success=True,
                    message="Invitation declined"
                )
                
        except Invitation.DoesNotExist:
            return RespondToInvitation(
                success=False,
                message="Invalid or expired invitation"
            )

class Mutation(graphene.ObjectType):
    create_university = CreateUniversity.Field()
    create_company = CreateCompany.Field()
    create_department = CreateDepartment.Field()
    create_invitation = CreateInvitation.Field()
    respond_to_invitation = RespondToInvitation.Field() 