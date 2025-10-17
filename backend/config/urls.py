from django.contrib import admin
from django.urls import path, include
from google.genai.types import AuthToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from apps.Users.views import RegisterUserView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.Users.urls')),
    path('api/habits/',include('apps.Habits.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='tokenn_verify'),
]
