from api import views as api_views 
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("user/token/", api_views.MyTokenObtainPairView.as_view()) , # for getting a JWT token (demands Authintication)
    path("user/token/refresh/", TokenRefreshView.as_view()),
    path("user/register/", api_views.RegisterView.as_view()),
    path('user/password-reset-email/<str:email>/', api_views.PasswordResetEmailVerifyAPIView.as_view()), # Get specific USER
    path("user/password-change/" , api_views.PasswordChangeAPIView.as_view())   # change password
]
