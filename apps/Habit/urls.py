from django.contrib import admin
from django.urls import path, include
from apps.Habit import views


urlpatterns = [
    path('inicio/', views.home_view, name="home_view")
    #path('/usuario/', include('apps.Users.urls'))
    ]

