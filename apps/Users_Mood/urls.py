from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserMoodViewSet

router = DefaultRouter()
router.register(r'moods', UserMoodViewSet, basename="mood")

urlpatterns = [
    path("", include(router.urls))
]