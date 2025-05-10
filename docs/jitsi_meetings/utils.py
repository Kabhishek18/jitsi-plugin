from django.conf import settings
from jitsi_py import JitsiClient, JitsiServerConfig, JitsiServerType
from jitsi_py.security.tokens import generate_jwt_token
import logging
import uuid

logger = logging.getLogger(__name__)

def get_jitsi_client():
    """Get a JitsiClient instance from Django settings"""
    jitsi_config = getattr(settings, "JITSI_CONFIG", {})
    
    server_type = jitsi_config.get("SERVER_TYPE", "public")
    server_config = JitsiServerConfig(
        server_type=JitsiServerType(server_type),
        domain=jitsi_config.get("DOMAIN", "meet.jit.si"),
        secure=jitsi_config.get("SECURE", True),
        api_endpoint=jitsi_config.get("API_ENDPOINT")
    )
    
    return JitsiClient(
        server_config=server_config,
        app_id=jitsi_config.get("APP_ID"),
        api_key=jitsi_config.get("API_KEY"),
        jwt_secret=jitsi_config.get("JWT_SECRET")
    )

def generate_user_token(user, room_name, role="viewer", expiry=3600):
    """Generate a JWT token for a Django user"""
    jwt_secret = getattr(settings, "JITSI_CONFIG", {}).get("JWT_SECRET")
    app_id = getattr(settings, "JITSI_CONFIG", {}).get("APP_ID")
    
    if not jwt_secret:
        logger.warning("No JWT_SECRET configured, cannot generate token")
        return None
    
    user_id = str(user.id) if user.id else str(uuid.uuid4())
    user_name = user.get_full_name() or user.username if user else "Guest"
    user_email = user.email if user and user.email else None
    user_avatar = getattr(user, 'avatar_url', None)
    
    try:
        return generate_jwt_token(
            jwt_secret=jwt_secret,
            app_id=app_id or "django-jitsi",
            room_name=room_name,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            user_avatar=user_avatar,
            role=role,
            expiry=expiry
        )
    except Exception as e:
        logger.error(f"Error generating JWT token: {str(e)}")
        return None

def send_meeting_invitations(meeting):
    """Send email invitations to meeting participants"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.urls import reverse
    
    # Get the absolute URL for joining (you'll need to adapt this to your URL structure)
    try:
        join_url = settings.SITE_URL + reverse('jitsi_meetings:join_scheduled_meeting', args=[meeting.id])
    except:
        # Fallback if SITE_URL not set
        join_url = f"/meetings/scheduled/{meeting.id}/join/"
        logger.warning("SITE_URL not set in settings, using relative URL for meeting invitation")
    
    context = {
        'meeting': meeting,
        'join_url': join_url,
        'host_name': meeting.created_by.get_full_name() or meeting.created_by.username,
    }
    
    # Get participants emails
    recipient_list = list(meeting.participants.values_list('email', flat=True))
    recipient_list = [email for email in recipient_list if email]  # Filter out empty emails
    
    if recipient_list:
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
            subject = f"Invitation: {meeting.title}"
            
            try:
                html_message = render_to_string('jitsi_meetings/email/meeting_invitation.html', context)
                plain_message = render_to_string('jitsi_meetings/email/meeting_invitation.txt', context)
            except:
                # Fallback if templates not found
                html_message = f"""
                <html>
                <body>
                    <h1>Meeting Invitation: {meeting.title}</h1>
                    <p>You have been invited to join a meeting.</p>
                    <p><strong>Title:</strong> {meeting.title}</p>
                    <p><strong>Start Time:</strong> {meeting.start_time}</p>
                    <p><strong>End Time:</strong> {meeting.end_time}</p>
                    <p><strong>Host:</strong> {context['host_name']}</p>
                    <p><a href="{join_url}">Click here to join the meeting</a></p>
                </body>
                </html>
                """
                plain_message = f"""
                Meeting Invitation: {meeting.title}
                
                You have been invited to join a meeting.
                
                Title: {meeting.title}
                Start Time: {meeting.start_time}
                End Time: {meeting.end_time}
                Host: {context['host_name']}
                
                Join URL: {join_url}
                """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False
            )
            logger.info(f"Sent invitations for meeting {meeting.id} to {len(recipient_list)} participants")
        except Exception as e:
            logger.error(f"Error sending meeting invitations: {str(e)}")