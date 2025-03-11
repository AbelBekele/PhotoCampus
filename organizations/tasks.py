from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils import timezone
from .models import Invitation
import logging
from celery.exceptions import MaxRetriesExceededError
from smtplib import SMTPException
import os

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_organization_invitation_email(self, invitation_id, email, first_name, organization_name, organization_type, invitation_token):
    """
    Send organization invitation email with retry logic.
    
    Args:
        invitation_id: ID of the invitation record
        email: Email address of the invitee
        first_name: First name of the invitee
        organization_name: Name of the organization (university or company)
        organization_type: Type of organization ("university" or "company")
        invitation_token: Unique token for accepting the invitation
    """
    logger.info(f"Starting invitation email task for {organization_type} invitation {invitation_id} to {email}")
    
    if not email:
        logger.error("Email validation failed: Empty email address")
        raise ValueError("Email address cannot be empty")
    
    try:
        validate_email(email)
        
        # Create email content (plain text fallback)
        subject = f'Invitation to join {organization_name} on PhotoCampus'
        message = (
            f"Hello {first_name},\n\n"
            f"You have been invited to join {organization_name} ({organization_type}) on PhotoCampus.\n\n"
            f"Please login to access your {organization_type}'s photo galleries.\n\n"
            f"Thank you!"
        )
        
        # Render the HTML template with context data
        context = {
            'first_name': first_name,
            'organization_name': organization_name,
            'organization_type': organization_type,
            'invitation_token': invitation_token,
            'login_url': f"{settings.SITE_URL}/invitation/{invitation_token}/"
        }
        
        html_message = render_to_string('email/invitation.html', context)
        
        logger.info(f"Attempting to send invitation email to {email}")
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Invitation email sent successfully to {email}")
        return f"Invitation email sent for {organization_type} {organization_name} to {email}"
        
    except (SMTPException, ConnectionError) as exc:
        try:
            logger.warning(f"Email sending failed, attempting retry {self.request.retries + 1} of 3")
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for sending invitation email to {email}")
            raise
    except ValidationError as e:
        logger.error(f"Email validation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending invitation email: {str(e)}", exc_info=True)
        raise

@shared_task
def process_pending_invitations():
    """
    Process pending invitations that haven't been sent emails yet or need to be re-sent.
    This task is scheduled to run periodically via Celery Beat.
    """
    # Find pending invitations that haven't been processed or need retry
    pending_invitations = Invitation.objects.filter(
        status='pending'
    ).filter(
        Q(email_sent=False) | 
        Q(last_email_attempt__lt=timezone.now() - timezone.timedelta(hours=24))
    ).select_related('university', 'company', 'inviter')
    
    logger.info(f"Found {pending_invitations.count()} pending invitations to process")
    
    for invitation in pending_invitations:
        try:
            # Determine organization details
            if invitation.university:
                organization_name = invitation.university.name
                organization_type = "university"
            elif invitation.company:
                organization_name = invitation.company.name
                organization_type = "company"
            else:
                logger.error(f"Invitation {invitation.id} has no organization")
                continue
            
            # Try to find a name for the recipient, otherwise use generic greeting
            first_name = "there"  # Default
            if invitation.invitee:
                if invitation.invitee.first_name:
                    first_name = invitation.invitee.first_name
            
            # Send the email
            send_organization_invitation_email.delay(
                invitation_id=invitation.id,
                email=invitation.email,
                first_name=first_name,
                organization_name=organization_name,
                organization_type=organization_type,
                invitation_token=str(invitation.token)
            )
            
            # Update invitation record to mark email as sent
            invitation.email_sent = True
            invitation.last_email_attempt = timezone.now()
            invitation.save(update_fields=['email_sent', 'last_email_attempt'])
            
            logger.info(f"Scheduled invitation email for invitation {invitation.id}")
            
        except Exception as e:
            logger.error(f"Error processing invitation {invitation.id}: {str(e)}", exc_info=True)
    
    return f"Processed {pending_invitations.count()} pending invitations"