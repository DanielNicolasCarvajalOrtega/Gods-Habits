from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.Habits.views import HabitViewSet

router = DefaultRouter()
router.register(r'habits',HabitViewSet, basename='habit')

urlpatterns = [
    path('',include(router.urls))
]

