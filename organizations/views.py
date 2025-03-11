from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import University, Company
from posts.models import Post

# Create your views here.

@login_required
def organization_detail(request, id):
    """View for displaying an organization's detail page with its posts."""
    # Try to find a university with this ID first
    university = None
    company = None
    organization = None
    organization_type = None

    try:
        university = University.objects.get(id=id)
        organization = university
        organization_type = 'university'
    except University.DoesNotExist:
        try:
            company = Company.objects.get(id=id)
            organization = company
            organization_type = 'company'
        except Company.DoesNotExist:
            # Handle case where no organization with this ID exists
            return render(request, 'organization_not_found.html', {'id': id})

    # Get posts related to this organization
    # This assumes you have a relationship between posts and organizations
    if organization_type == 'university':
        posts = Post.objects.filter(author__organization_memberships__university=university).order_by('-created_at')
    else:
        posts = Post.objects.filter(author__organization_memberships__company=company).order_by('-created_at')

    context = {
        'organization': organization,
        'organization_type': organization_type,
        'posts': posts,
    }

    return render(request, 'organization_detail.html', context)
