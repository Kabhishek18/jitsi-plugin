from django.urls import path
from . import views

app_name = 'jitsi_meetings'

urlpatterns = [
    # Simple meeting creation without authentication
    path('simple/create/', views.create_meeting, name='create_simple_meeting'),
    path('simple/join/<str:room_name>/', views.join_meeting, name='join_simple_meeting'),
    
    # Authenticated meeting management
    path('', views.room_list, name='room_list'),
    path('create/', views.room_create, name='room_create'),
    path('<uuid:pk>/', views.room_detail, name='room_detail'),
    path('<uuid:pk>/update/', views.room_update, name='room_update'),
    path('<uuid:pk>/delete/', views.room_delete, name='room_delete'),
    path('<uuid:pk>/advanced/', views.advanced_meeting, name='advanced_meeting'),
    
    # Scheduled meetings
    path('<uuid:pk>/schedule/', views.schedule_meeting, name='schedule_meeting'),
    path('scheduled/', views.my_scheduled_meetings, name='my_scheduled_meetings'),
    path('scheduled/<int:meeting_id>/join/', views.join_scheduled_meeting, name='join_scheduled_meeting'),
    
    # Webhook
    path('webhooks/', views.webhook_handler, name='webhook_handler'),
]