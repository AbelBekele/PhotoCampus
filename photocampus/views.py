from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse

class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with email and name fields"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

def register_view(request):
    """View for handling user registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """View for handling user login"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Check if there's an invitation token in the session
                invitation_token = request.session.get('invitation_token')
                auto_accept = request.session.get('auto_accept', False)
                
                if invitation_token and auto_accept:
                    # Clear the session variables
                    del request.session['invitation_token']
                    del request.session['auto_accept']
                    
                    # Redirect to the invitation URL with the accept parameter
                    return redirect(f'/invitation/{invitation_token}/?accept=true')
                    
                next_url = request.POST.get('next', '/')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {
        'form': form,
        'next': request.GET.get('next', '/')
    })

def invitation_view(request, token):
    """
    View for handling invitation links.
    This view checks the invitation token and redirects to the login page.
    If the user is already logged in and the accept=true parameter is present, 
    it will automatically accept the invitation.
    """
    from organizations.models import Invitation
    from django.utils import timezone
    
    try:
        # Try to get the invitation
        invitation = Invitation.objects.get(token=token, status='pending')
        
        # Check if the user is logged in
        if request.user.is_authenticated:
            # If the user is logged in and the accept parameter is true, accept the invitation
            if request.GET.get('accept') == 'true':
                # Check if the invitation is for this user
                if invitation.email == request.user.email:
                    from organizations.models import OrganizationMembership
                    
                    # Create membership
                    membership = OrganizationMembership(
                        user=request.user,
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
                    invitation.invitee = request.user
                    invitation.responded_at = timezone.now()
                    invitation.save()
                    
                    messages.success(request, f'You have successfully joined {invitation.university.name if invitation.university else invitation.company.name}!')
                    
                    # Redirect to home
                    return redirect('home')
                else:
                    messages.error(request, 'This invitation is not for your email address')
            
            # Redirect to home if already logged in
            return redirect('home')
        
        # Store the token in the session to use after login
        request.session['invitation_token'] = str(token)
        request.session['auto_accept'] = request.GET.get('accept') == 'true'
        
        # Redirect to login with next URL set to invitation URL
        return redirect(f'/accounts/login/?next=/invitation/{token}/')
        
    except Invitation.DoesNotExist:
        messages.error(request, 'Invalid or expired invitation')
        return redirect('login') 