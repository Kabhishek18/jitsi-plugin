# Jitsi Meetings Django App

This Django app integrates with the Jitsi-Py package to provide complete video conferencing capabilities for your Django project.

## Features

- Create and join video meetings without authentication
- User authentication and meeting room management
- Meeting scheduling with email notifications
- WebRTC-based video conferencing with audio/video controls
- Advanced meeting features (screen sharing, recording, etc.)
- Webhook handling for real-time events

## Installation

1. Install the required packages:

   ```bash
   pip install jitsi-py[django]
   ```

2. Add 'jitsi_meetings' to your INSTALLED_APPS in settings.py:

   ```python
   INSTALLED_APPS = [
       # ...
       'jitsi_meetings',
       # ...
   ]
   ```

3. Add Jitsi-Py configuration to your settings.py:

   ```python
   # Jitsi configuration
   JITSI_CONFIG = {
       'SERVER_TYPE': 'public',  # Use 'self_hosted' for your own server
       'DOMAIN': 'meet.jit.si',  # Default public server
       'SECURE': True,
       # 'API_ENDPOINT': 'https://your-api-endpoint.com',  # Uncomment for custom API endpoint
       # 'APP_ID': 'your_app_id',  # Uncomment for JWT authentication
       # 'JWT_SECRET': 'your_jwt_secret',  # Uncomment for JWT authentication
   }
   
   # Optional - for email notifications
   # DEFAULT_FROM_EMAIL = 'noreply@example.com'
   # SITE_URL = 'https://example.com'  # Used for building absolute URLs
   ```

4. Include the app's URLs in your main urls.py:

   ```python
   from django.urls import path, include

   urlpatterns = [
       # ...
       path('meetings/', include('jitsi_meetings.urls')),
       # ...
   ]
   ```

5. Run migrations:

   ```bash
   python manage.py makemigrations jitsi_meetings
   python manage.py migrate
   ```

## Usage

### Quick Meeting (No Authentication)

For quick meetings without user accounts, use:
- `/meetings/simple/create/` - Create a new meeting
- `/meetings/simple/join/<room_name>/` - Join an existing meeting

### Authenticated Meeting Rooms

For registered users:
- `/meetings/` - List all meeting rooms
- `/meetings/create/` - Create a new room
- `/meetings/<uuid>/` - View room details
- `/meetings/<uuid>/advanced/` - Join with advanced features

### Scheduled Meetings

For calendar-based scheduling:
- `/meetings/<uuid>/schedule/` - Schedule a meeting in a room
- `/meetings/scheduled/` - View all scheduled meetings
- `/meetings/scheduled/<id>/join/` - Join a scheduled meeting

## Templates

The app includes ready-to-use templates that you can override in your own project. The templates use Bootstrap 5 for styling.

To override a template, create a file with the same path in your project's templates directory:

```
templates/
└── jitsi_meetings/
    ├── base.html  # Base template for the app
    ├── room_list.html
    ├── room_detail.html
    # etc.
```

## Customization

### Settings

- `JITSI_CONFIG`: Main configuration for Jitsi servers and authentication
- `JITSI_VERIFY_WEBHOOK_JWT`: Whether to verify JWT tokens in webhook requests (default: False)

### Advanced Features

For advanced features like recording, you'll need:
1. A self-hosted Jitsi server
2. JWT authentication enabled
3. Proper configuration of your Jitsi server to accept webhooks

## Directory Structure

```
jitsi_meetings/
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── signals.py
├── urls.py
├── utils.py
├── views.py
└── templates/
    └── jitsi_meetings/
        ├── base.html
        ├── room_list.html
        └── ...
```

## Troubleshooting

### Common Issues

1. **Select2 Not Working**: If the participant selector in scheduled meetings doesn't work, make sure jQuery is loaded before Select2.

2. **JavaScript Errors**: For issues with the Jitsi API, check the browser console for errors.

3. **JWT Authentication**: Make sure your JWT secret matches between Django and your Jitsi server.

4. **Email Notifications**: Ensure Django's email settings are properly configured.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Built with Jitsi-Py, a Python package for Jitsi Meet integration.# Jitsi Meetings Django App

This Django app integrates with the Jitsi-Py package to provide complete video conferencing capabilities for your Django project.

## Features

- Create and join video meetings without authentication
- User authentication and meeting room management
- Meeting scheduling with email notifications
- WebRTC-based video conferencing with audio/video controls
- Advanced meeting features (screen sharing, recording, etc.)
- Webhook handling for real-time events

## Installation

1. Install the required packages:

   ```bash
   pip install jitsi-py[django]
   ```

2. Add 'jitsi_meetings' to your INSTALLED_APPS in settings.py:

   ```python
   INSTALLED_APPS = [
       # ...
       'jitsi_meetings',
       # ...
   ]
   ```

3. Add Jitsi-Py configuration to your settings.py:

   ```python
   # Jitsi configuration
   JITSI_CONFIG = {
       'SERVER_TYPE': 'public',  # Use 'self_hosted' for your own server
       'DOMAIN': 'meet.jit.si',  # Default public server
       'SECURE': True,
       # 'API_ENDPOINT': 'https://your-api-endpoint.com',  # Uncomment for custom API endpoint
       # 'APP_ID': 'your_app_id',  # Uncomment for JWT authentication
       # 'JWT_SECRET': 'your_jwt_secret',  # Uncomment for JWT authentication
   }
   
   # Optional - for email notifications
   # DEFAULT_FROM_EMAIL = 'noreply@example.com'
   # SITE_URL = 'https://example.com'  # Used for building absolute URLs
   ```

4. Include the app's URLs in your main urls.py:

   ```python
   from django.urls import path, include

   urlpatterns = [
       # ...
       path('meetings/', include('jitsi_meetings.urls')),
       # ...
   ]
   ```

5. Run migrations:

   ```bash
   python manage.py makemigrations jitsi_meetings
   python manage.py migrate
   ```

## Usage

### Quick Meeting (No Authentication)

For quick meetings without user accounts, use:
- `/meetings/simple/create/` - Create a new meeting
- `/meetings/simple/join/<room_name>/` - Join an existing meeting

### Authenticated Meeting Rooms

For registered users:
- `/meetings/` - List all meeting rooms
- `/meetings/create/` - Create a new room
- `/meetings/<uuid>/` - View room details
- `/meetings/<uuid>/advanced/` - Join with advanced features

### Scheduled Meetings

For calendar-based scheduling:
- `/meetings/<uuid>/schedule/` - Schedule a meeting in a room
- `/meetings/scheduled/` - View all scheduled meetings
- `/meetings/scheduled/<id>/join/` - Join a scheduled meeting

## Templates

The app includes ready-to-use templates that you can override in your own project. The templates use Bootstrap 5 for styling.

To override a template, create a file with the same path in your project's templates directory:

```
templates/
└── jitsi_meetings/
    ├── base.html  # Base template for the app
    ├── room_list.html
    ├── room_detail.html
    # etc.
```

## Customization

### Settings

- `JITSI_CONFIG`: Main configuration for Jitsi servers and authentication
- `JITSI_VERIFY_WEBHOOK_JWT`: Whether to verify JWT tokens in webhook requests (default: False)

### Advanced Features

For advanced features like recording, you'll need:
1. A self-hosted Jitsi server
2. JWT authentication enabled
3. Proper configuration of your Jitsi server to accept webhooks

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Built with Jitsi-Py, a Python package for Jitsi Meet integration.