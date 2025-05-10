from django.apps import AppConfig


class JitsiMeetingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jitsi_meetings'
    verbose_name = 'Jitsi Meetings'
    
    def ready(self):
        # Import signals handlers
        import jitsi_meetings.signals