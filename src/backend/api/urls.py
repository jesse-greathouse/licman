from django.urls import path
from . import views  # Import your API views here

urlpatterns = [
    path("ping/", views.ping, name="api-ping"),
]
