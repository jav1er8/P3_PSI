"""
ASGI config for mychess project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mychess.settings')

# get_asgi_application() should go BEFORE import models!! 
django_asgi_app = get_asgi_application()

from models.routing import websocket_urlpatterns


# application = get_asgi_application()
application = ProtocolTypeRouter({
		"http": django_asgi_app,
		"websocket": AuthMiddlewareStack(
				URLRouter(websocket_urlpatterns) # Si llega una peticion websocket -> la maneja el websocket_urlpatterns
		),
})
