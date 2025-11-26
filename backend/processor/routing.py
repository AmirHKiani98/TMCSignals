from django.urls import path
from api.consumers import FileFindConsumer

websocket_urlpatterns = [
    path("ws/find_file/<str:sig_id>/", FileFindConsumer.as_asgi()),
]