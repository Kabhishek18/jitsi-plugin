
from django import forms
from .models import JitsiRoom, ScheduledMeeting
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class JitsiRoomForm(forms.ModelForm):
    """Form for creating and editing meeting rooms"""
    duration_hours = forms.IntegerField(
        required=False, 
        min_value=1, 
        max_value=24,
        label="Duration (hours)",
        help_text="Room duration in hours (optional)"
    )
    
    class Meta:
        model = JitsiRoom
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a unique room name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'}),
        }
        help_texts = {
            'name': 'Letters, numbers, and hyphens only. This will be used in the meeting URL.',
        }
    
    def clean_name(self):
        """Ensure room name is URL-friendly"""
        name = self.cleaned_data.get('name')
        if name:
            # Replace spaces with hyphens and convert to lowercase
            name = name.replace(' ', '-').lower()
        return name


class ScheduleMeetingForm(forms.ModelForm):
    """Form for scheduling meetings"""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        initial=timezone.now().time
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        initial=(timezone.now() + timedelta(hours=1)).time
    )
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        help_text="Select participants to invite (optional)"
    )
    
    class Meta:
        model = ScheduledMeeting
        fields = ['title', 'recurring', 'recurrence_pattern']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter meeting title'}),
            'recurrence_pattern': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            # Exclude current user from participants
            self.fields['participants'].queryset = User.objects.exclude(id=self.user.id)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        end_date = cleaned_data.get('end_date')
        end_time = cleaned_data.get('end_time')
        recurring = cleaned_data.get('recurring')
        recurrence_pattern = cleaned_data.get('recurrence_pattern')
        
        if recurring and recurrence_pattern == 'none':
            self.add_error('recurrence_pattern', 'Please select a recurrence pattern for recurring meetings.')
        
        if all([start_date, start_time, end_date, end_time]):
            start_datetime = timezone.make_aware(
                datetime.combine(start_date, start_time)
            )
            end_datetime = timezone.make_aware(
                datetime.combine(end_date, end_time)
            )
            
            if start_datetime >= end_datetime:
                raise forms.ValidationError("End time must be after start time.")
            
            if start_datetime < timezone.now():
                raise forms.ValidationError("Meeting cannot be scheduled in the past.")
            
            cleaned_data['start_datetime'] = start_datetime
            cleaned_data['end_datetime'] = end_datetime
        
        return cleaned_data


class JoinMeetingForm(forms.Form):
    """Simple form for joining a meeting"""
    display_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your display name'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email (optional)'})
    )
    role = forms.ChoiceField(
        choices=[('viewer', 'Participant'), ('host', 'Host')],
        initial='viewer',
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )