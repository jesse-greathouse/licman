from rest_framework.routers import DefaultRouter
from .viewsets import HelloViewSet

router = DefaultRouter()
router.register(r'hello', HelloViewSet, basename='hello')
