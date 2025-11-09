from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterViewSet, LoginView, MeViewSet,
    RoomViewSet, GalleryViewSet, BookingViewSet, RoomCategoryViewSet,
)

router = DefaultRouter()
router.register(r"auth/register", RegisterViewSet, basename="register")
router.register(r"auth/me", MeViewSet, basename="me")
router.register(r"rooms", RoomViewSet)
router.register(r"gallery", GalleryViewSet)
router.register(r"bookings", BookingViewSet)
router.register(r'categories', RoomCategoryViewSet)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
