from django.urls import re_path
from .consumers import ChessConsumer

websocket_urlpatterns = [
    # Las peticiones http://localhost:8000/ws/chat/room_name/
    # seran manejadas por el Consumer
    # re_path(r'ws:\\host/ws/play/<int:gameID>/token/', ChessConsumer.as_asgi()),
    re_path(r'ws/play/(?P<gameID>\d+)/?', ChessConsumer.as_asgi()),
]
