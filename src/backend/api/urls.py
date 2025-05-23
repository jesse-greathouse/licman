from django.urls import path, include
from .views import PingAPIView
from .routers import router

urlpatterns = [
    path('', include(router.urls)),
    path('ping/', PingAPIView.as_view(), name='api-ping'),
]
