from django.urls import path
from .views import find_file_view, get_intersections

app_name = "api"


# Common endpoints: root and health. Add more routes in your app's views module
# and they will be picked up automatically.
urlpatterns = [
    path("get_intersections/", get_intersections, name="get-intersections"),
    path("find_file/", find_file_view, name="find-file"),
]