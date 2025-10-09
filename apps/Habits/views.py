from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Habits, Habit_execution
from serializers import *
from .services import HabitService


def home_view(request):
    return render(request, 'index.html')

class HabitViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo usuarios autenticados"""
        return HabitService.get_user_habits(self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return HabitListSerializer
        elif self.action == 'create':
            return HabitCreateSerializer
        return HabitSerializers


    def list_user_habits(self, request):
        pass