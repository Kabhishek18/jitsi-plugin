# jitsi_py/integrations/django.py

from django.conf import settings
from django.urls import path
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging

from ..core.client import JitsiClient, JitsiServerConfig, JitsiServerType
from ..security.tokens import verify_jwt_token

logger = logging.getLogger("jitsi_py.django")

def get_jitsi_client():
    """Get a JitsiClient instance from Django settings."""
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

@csrf_exempt
@require_POST
def webhook_handler(request):
    """Handle Jitsi webhook events."""
    try:
        payload = json.loads(request.body)
        
        # Verify JWT token if enabled
        if getattr(settings, "JITSI_VERIFY_WEBHOOK_JWT", False):
            jwt_secret = getattr(settings, "JITSI_JWT_SECRET", "")
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            
            if not token or not verify_jwt_token(token, jwt_secret).is_valid:
                return JsonResponse({"error": "Invalid token"}, status=401)
        
        # Process the event
        event_type = payload.get("eventType")
        
        # Call the appropriate handler
        handler_name = f"handle_{event_type}"
        if hasattr(settings, "JITSI_EVENT_HANDLERS") and handler_name in settings.JITSI_EVENT_HANDLERS:
            handler = settings.JITSI_EVENT_HANDLERS[handler_name]
            handler(payload)
        
        return JsonResponse({"status": "ok"})
    except Exception as e:
        logger.exception(f"Error processing webhook: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

def jitsi_urls():
    """Get URLs for Jitsi integration."""
    return [
        path("jitsi/webhooks/", webhook_handler, name="jitsi_webhook_handler"),
    ]