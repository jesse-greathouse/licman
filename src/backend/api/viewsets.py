from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet

class HelloViewSet(ViewSet):
    def list(self, request):
        return Response({'message': 'Hello from DRF ViewSet'})
