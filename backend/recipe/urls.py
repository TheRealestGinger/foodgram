from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DownloadShoppingCartView,
    IngredientViewSet,
    RecipeShortLinkView,
    RecipeViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path(
        'recipes/<int:id>/get-link/',
        RecipeShortLinkView.as_view(),
        name='recipe-short-link'
    ),
    path(
        'recipes/download_shopping_cart/',
        DownloadShoppingCartView.as_view(),
        name='download-shopping-cart'
    ),
] + router.urls
