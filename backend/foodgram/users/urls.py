from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SetPasswordView,
    AvatarView,
    UserViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path(
        'users/set_password/',
        SetPasswordView.as_view(),
        name='set_password'
    ),
    path('users/me/avatar/', AvatarView.as_view(), name='avatar'),
    path('auth/', include('djoser.urls.authtoken')),
] + router.urls
