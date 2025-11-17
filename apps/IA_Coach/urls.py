from django.urls import path
from .views import RecommendationsView

urlpatterns = [
    path("coach/recommendations/", RecommendationsView.as_view(), name="coach-recommendations"),
]
