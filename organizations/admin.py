from django.contrib import admin
from .models import University, Company, Department, OrganizationMembership, Invitation

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'founded_year', 'is_private', 'created_at')
    list_filter = ('is_private', 'created_at', 'location')
    search_fields = ('name', 'description', 'website')
    date_hierarchy = 'created_at'
    filter_horizontal = ('admins',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'company_size', 'is_private', 'created_at')
    list_filter = ('is_private', 'created_at', 'industry')
    search_fields = ('name', 'description', 'website', 'industry')
    date_hierarchy = 'created_at'
    filter_horizontal = ('admins',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'university')
    list_filter = ('university',)
    search_fields = ('name', 'description', 'university__name')

@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'university', 'company', 'department', 'role', 'joined_at')
    list_filter = ('role', 'joined_at', 'department')
    search_fields = ('user__username', 'user__email', 'role',
                    'university__name', 'company__name', 'department__name')
    date_hierarchy = 'joined_at'

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'inviter', 'university', 'company', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('email', 'inviter__username', 'university__name', 'company__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('token',)
