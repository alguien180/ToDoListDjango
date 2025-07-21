from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tasks/", include("Task.urls")),       # Task-related views
    path("accounts/", include("security.urls")),  # Login, logout, register
]

# Optional: Redirect root `/` to login or dashboard
from django.shortcuts import redirect
urlpatterns += [
    path("", lambda request: redirect("login"))  # or "task_manager"
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
