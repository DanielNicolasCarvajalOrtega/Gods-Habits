from pkgutil import get_data

from django.contrib.auth.management.commands.changepassword import UserModel
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.relations import method_overridden
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from yaml import serialize

from .models import UserMood
from .serializers import UserMoodSerializers
from .services import UserMoodService

class UserMoodViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserMoodSerializers

    def get_queryset(self):
        return UserMood.objects.filter(user=self.request.user)

    def create(self, request, *args , **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = UserMoodService.upsert_mood(request.user, serializer.validated_data)
        return Response(
            self.get_serializer(obj).data,
            status= status.HTTP_201_CREATED,
            )

    @action(detail=False, methods=["get"])
    def today(self, request):
        today = timezone.now().date()
        obj = UserMood.objects.filter(user=request.user, date=today).first()
        if not obj:
            return Response(
                {
                    "detail": "No hay registro de hoy!"
                }, status=200
            )
        return Response(self.get_serializer(obj).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        days = int(request.query_params.get("days",7))
        data = UserMoodService.get_stars(request.user, days=days)
        return Response(data)