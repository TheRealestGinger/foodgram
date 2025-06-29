from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('r/<int:pk>/', include('recipe.urls')),
] + router.urls
