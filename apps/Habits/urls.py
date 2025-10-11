from django.urls import path
from apps.Habits import views


urlpatterns = [
    path('inicio/',views.home_view, name="home_view"),
]

