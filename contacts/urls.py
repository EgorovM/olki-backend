from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContactRequestViewSet

router = DefaultRouter()
router.register(r"", ContactRequestViewSet, basename="contact")

urlpatterns = [
    path("", include(router.urls)),
]
