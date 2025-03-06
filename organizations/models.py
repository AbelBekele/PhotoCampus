from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Organization(models.Model):
    """Base model for all organizations (abstract)"""
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Note: Subclasses will define their own admins field with specific related_names
    
    # Is this organization page public or private?
    is_private = models.BooleanField(default=False, db_index=True,
                                    help_text="If private, only invited members can access")
    
    class Meta:
        abstract = True
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_private']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name

class University(Organization):
    """Model representing a university"""
    location = models.CharField(max_length=255, blank=True, db_index=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    
    # Administrators who can manage this university
    admins = models.ManyToManyField(User, related_name='administered_universities')
    
    # Departments or faculties
    class Meta:
        verbose_name_plural = "Universities"
        indexes = [
            models.Index(fields=['location']),
        ]

class Company(Organization):
    """Model representing a company or photography studio"""
    industry = models.CharField(max_length=100, blank=True, db_index=True)
    company_size = models.CharField(max_length=50, blank=True,
                                   help_text="e.g. Small (1-50), Medium (51-200), Large (201+)")
    
    # Administrators who can manage this company
    admins = models.ManyToManyField(User, related_name='administered_companies')
    
    class Meta:
        verbose_name_plural = "Companies"
        indexes = [
            models.Index(fields=['industry']),
        ]

class Department(models.Model):
    """Model representing a department or faculty within a university"""
    name = models.CharField(max_length=255, db_index=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='departments', db_index=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.university.name}"
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'university']),
        ]

class OrganizationMembership(models.Model):
    """Model representing a user's membership in an organization"""
    # Can be either University or Company
    university = models.ForeignKey(University, on_delete=models.CASCADE, 
                                 related_name='memberships', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, 
                               related_name='memberships', null=True, blank=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships', db_index=True)
    
    # For university members
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, 
                                 related_name='members', null=True, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    
    # For any member
    role = models.CharField(max_length=100, blank=True,
                           help_text="e.g. Student, Faculty, Staff, Employee, etc.")
    
    joined_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    def __str__(self):
        org_name = self.university.name if self.university else self.company.name
        return f"{self.user.username} @ {org_name}"
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'university']),
            models.Index(fields=['user', 'company']),
            models.Index(fields=['joined_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(university__isnull=False) | models.Q(company__isnull=False),
                name='must_belong_to_one_organization'
            )
        ]

class Invitation(models.Model):
    """Model for inviting users to private organizations"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    )
    
    # Unique identifier for the invitation
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    # Can be either University or Company
    university = models.ForeignKey(University, on_delete=models.CASCADE, 
                                 related_name='invitations', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, 
                              related_name='invitations', null=True, blank=True)
    
    # Who created the invitation
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations', db_index=True)
    
    # Email of the person being invited (they might not be a user yet)
    email = models.EmailField(db_index=True)
    
    # If the invited person is already a user
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, 
                              related_name='received_invitations', null=True, blank=True)
    
    role = models.CharField(max_length=100, blank=True,
                          help_text="Intended role in the organization")
    
    # For university invites
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, 
                                 null=True, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    
    # Invitation details
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        org_name = self.university.name if self.university else self.company.name
        return f"Invitation to {org_name} for {self.email}"
    
    class Meta:
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(university__isnull=False) | models.Q(company__isnull=False),
                name='invitation_must_belong_to_one_organization'
            )
        ]
