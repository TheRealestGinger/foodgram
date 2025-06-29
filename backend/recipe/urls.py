from django.urls import path

from .views import ShortLinkRedirectView

urlpatterns = [
    path('', ShortLinkRedirectView.as_view(), name='recipe-short-link'),
]
