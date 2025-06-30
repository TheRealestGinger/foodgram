from django.urls import path

from .views import short_link_redirect


namespace = 'recipe'

urlpatterns = [
    path('s/<int:recipe_id>/', short_link_redirect, name='recipe-short-link'),
]
