from django.contrib import admin
from .models import JitsiRoom, MeetingParticipant, MeetingRecording, ScheduledMeeting


class MeetingParticipantInline(admin.TabularInline):
    model = MeetingParticipant
    extra = 0


class MeetingRecordingInline(admin.TabularInline):
    model = MeetingRecording
    extra = 0


class ScheduledMeetingInline(admin.TabularInline):
    model = ScheduledMeeting
    extra = 0
    fields = ('title', 'start_time', 'end_time', 'recurring', 'recurrence_pattern')


@admin.register(JitsiRoom)
class JitsiRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'expires_at', 'is_active', 'is_expired')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    date_hierarchy = 'created_at'
    inlines = [ScheduledMeetingInline, MeetingParticipantInline, MeetingRecordingInline]
    
    def is_expired(self, obj):
        return obj.is_expired
    
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'room', 'role', 'joined_at', 'left_at', 'is_present')
    list_filter = ('is_present', 'role', 'joined_at')
    search_fields = ('display_name', 'participant_id', 'room__name')
    date_hierarchy = 'joined_at'


@admin.register(MeetingRecording)
class MeetingRecordingAdmin(admin.ModelAdmin):
    list_display = ('room', 'recording_id', 'start_time', 'end_time', 'status', 'duration_formatted')
    list_filter = ('status', 'start_time')
    search_fields = ('recording_id', 'room__name')
    date_hierarchy = 'start_time'


@admin.register(ScheduledMeeting)
class ScheduledMeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'room', 'start_time', 'end_time', 'recurring', 'recurrence_pattern', 'created_by')
    list_filter = ('recurring', 'recurrence_pattern', 'start_time')
    search_fields = ('title', 'room__name', 'created_by__username')
    date_hierarchy = 'start_time'
    filter_horizontal = ('participants',)