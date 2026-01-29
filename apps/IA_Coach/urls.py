from django.urls import path
from . import views

urlpatterns = [
    path("advice/",views.get_personalized_advice,name ='get_advice'),
    path("context/", views.get_user_context, name='get_context'),
    path("coach/recommendations/", views.RecommendationsView.as_view(), name="coach-recommendations"),
]
