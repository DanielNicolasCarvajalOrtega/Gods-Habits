from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.Habits.views import HabitViewSet
from apps.Users.views import RegisterUserView

router = DefaultRouter()
router.register(r'',HabitViewSet, basename='user')


urlpatterns = [
    path('',include(router.urls)),
    path('auth/register/', RegisterUserView.as_view(), name="register"),
]

