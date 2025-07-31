from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers # for the serializers 
from Task.views import NoteAPIView #Serializer

router =routers.DefaultRouter()
router.register(r'notes',NoteAPIView,'NoteAPIView')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("Task.urls")),       # Task-related views
    path("", include("security.urls")),  # Login, logout, register
    path("api/",include(router.urls)), #this is how we link lines 8-9 to the gral url.
    path("api-auth/",include('rest_framework.urls',namespace='rest_framework')) #the OG way to addit
]

# Optional: Redirect root `/` to login or dashboard
from django.shortcuts import redirect
urlpatterns += [
    path("", lambda request: redirect("login"))  # or "task_manager"
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)