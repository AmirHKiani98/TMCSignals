from django.urls import path
from .views import find_file_live_view, find_file_view, get_intersections, get_snapshot_view

app_name = "api"


# Common endpoints: root and health. Add more routes in your app's views module
# and they will be picked up automatically.
urlpatterns = [
    path("get_intersections/", get_intersections, name="get-intersections"),
    path("find_file/", find_file_view, name="find-file"),
    path("find_file_live/", find_file_live_view, name="find-file-live"),
    path("stream_find_files/<str:sig_id>/", find_file_live_view, name="stream-find-files"),
    path("get-snapshot/", get_snapshot_view, name="get-snapshot"),
]