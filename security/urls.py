from django.urls import path
from .views import CustomLoginView, RegisterView, LogoutRedirectView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutRedirectView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
]
