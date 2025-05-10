from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from datetime import timedelta
import json
import uuid
import logging

from .models import JitsiRoom, MeetingParticipant, MeetingRecording, ScheduledMeeting
from .forms import JitsiRoomForm, ScheduleMeetingForm, JoinMeetingForm
from .utils import get_jitsi_client, generate_user_token, send_meeting_invitations

logger = logging.getLogger(__name__)

# Simple meeting views
def create_meeting(request):
    """Create a simple meeting without authentication"""
    if request.method == 'POST':
        display_name = request.POST.get('display_name', 'Guest')
        
        # Generate a unique room name
        room_name = f"meeting-{uuid.uuid4().hex[:8]}"
        
        # Get Jitsi client
        client = get_jitsi_client()
        
        # Create a room
        room = client.create_room(room_name)
        
        # Generate URL for the user
        join_url = room.join_url(user_name=display_name)
        
        return render(request, 'jitsi_meetings/simple_meeting.html', {
            'room_name': room_name,
            'join_url': join_url,
            'display_name': display_name
        })
    
    return render(request, 'jitsi_meetings/create_simple.html')

def join_meeting(request, room_name):
    """Join an existing meeting"""
    if request.method == 'POST':
        form = JoinMeetingForm(request.POST)
        if form.is_valid():
            display_name = form.cleaned_data['display_name']
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            
            # Get Jitsi client
            client = get_jitsi_client()
            room = client.get_room(room_name)
            
            # Generate URL based on role
            if role == 'host':
                join_url = room.host_url(user_name=display_name)
            else:
                join_url = room.join_url(user_name=display_name, user_email=email)
            
            return render(request, 'jitsi_meetings/join.html', {
                'room_name': room_name,
                'join_url': join_url,
                'display_name': display_name
            })
    else:
        form = JoinMeetingForm()
    
    return render(request, 'jitsi_meetings/join_form.html', {
        'form': form,
        'room_name': room_name
    })

# Authenticated meeting management
@login_required
def room_list(request):
    """List rooms created by the current user"""
    rooms = JitsiRoom.objects.filter(created_by=request.user, is_active=True)
    upcoming_meetings = ScheduledMeeting.objects.filter(
        participants=request.user,
        start_time__gt=timezone.now()
    ).order_by('start_time')[:5]
    
    return render(request, 'jitsi_meetings/room_list.html', {
        'rooms': rooms,
        'upcoming_meetings': upcoming_meetings
    })

@login_required
def room_create(request):
    """Create a new meeting room"""
    if request.method == 'POST':
        form = JitsiRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            
            # Set expiry if specified
            if form.cleaned_data.get('duration_hours'):
                hours = form.cleaned_data.get('duration_hours')
                room.expires_at = timezone.now() + timedelta(hours=hours)
            
            room.save()
            messages.success(request, f"Room '{room.name}' created successfully")
            return redirect('jitsi_meetings:room_detail', pk=room.id)
    else:
        form = JitsiRoomForm()
    
    return render(request, 'jitsi_meetings/room_form.html', {'form': form})

@login_required
def room_detail(request, pk):
    """View room details and join options"""
    room = get_object_or_404(JitsiRoom, pk=pk)
    
    # Check if user has permission to access this room
    if room.created_by != request.user and not request.user.is_staff:
        scheduled_meetings = ScheduledMeeting.objects.filter(
            room=room,
            participants=request.user
        )
        if not scheduled_meetings.exists():
            messages.error(request, "You don't have permission to access this room")
            return redirect('jitsi_meetings:room_list')
    
    host_url = room.generate_host_url(request.user.get_full_name() or request.user.username)
    guest_url = room.generate_guest_url()
    
    # Get upcoming scheduled meetings for this room
    scheduled_meetings = ScheduledMeeting.objects.filter(
        room=room,
        start_time__gt=timezone.now()
    ).order_by('start_time')
    
    return render(request, 'jitsi_meetings/room_detail.html', {
        'room': room,
        'host_url': host_url,
        'guest_url': guest_url,
        'scheduled_meetings': scheduled_meetings
    })

@login_required
def room_update(request, pk):
    """Update room details"""
    room = get_object_or_404(JitsiRoom, pk=pk, created_by=request.user)