from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid


class JitsiRoom(models.Model):
    """Model for Jitsi meeting rooms"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_rooms')
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def generate_host_url(self, user_name=None):
        from .utils import get_jitsi_client
        client = get_jitsi_client()
        room = client.get_room(self.name)
        return room.host_url(user_name=user_name or self.created_by.get_full_name() or self.created_by.username)
    
    def generate_guest_url(self, user_name=None):
        from .utils import get_jitsi_client
        client = get_jitsi_client()
        room = client.get_room(self.name)
        return room.join_url(user_name=user_name)


class MeetingParticipant(models.Model):
    """Model to track meeting participants"""
    room = models.ForeignKey(JitsiRoom, on_delete=models.CASCADE, related_name='participants')
    participant_id = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=50, default='viewer')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(blank=True, null=True)
    is_present = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['room', 'participant_id']
    
    def __str__(self):
        return f"{self.display_name or self.participant_id} - {self.room.name}"


class MeetingRecording(models.Model):
    """Model to track meeting recordings"""
    STATUS_CHOICES = [
        ('recording', 'Recording'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    room = models.ForeignKey(JitsiRoom, on_delete=models.CASCADE, related_name='recordings')
    recording_id = models.CharField(max_length=255, unique=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recording')
    file_url = models.URLField(blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    duration = models.PositiveIntegerField(blank=True, null=True)  # Duration in seconds
    
    def __str__(self):
        return f"Recording {self.recording_id} - {self.room.name}"
    
    @property
    def duration_formatted(self):
        """Format duration as HH:MM:SS."""
        if not self.duration:
            return "00:00:00"
        
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"


class ScheduledMeeting(models.Model):
    """Model for scheduled meetings"""
    RECURRENCE_CHOICES = [
        ('none', 'None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    room = models.ForeignKey(JitsiRoom, on_delete=models.CASCADE, related_name='schedules')
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, choices=RECURRENCE_CHOICES, default='none')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='scheduled_meetings', blank=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    @property
    def is_upcoming(self):
        now = timezone.now()
        return now < self.start_time
    
    @property
    def is_past(self):
        now = timezone.now()
        return now > self.end_time