from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import logging

from .models import ScheduledMeeting
from .utils import send_meeting_invitations

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ScheduledMeeting)
def handle_scheduled_meeting_save(sender, instance, created, **kwargs):
    """Handle sending invitations when a scheduled meeting is created or updated"""
    if created:
        # Send invitations when a new meeting is created
        try:
            if instance.participants.exists():
                send_meeting_invitations(instance)
        except Exception as e:
            logger.error(f"Error sending invitations for scheduled meeting {instance.id}: {str(e)}")