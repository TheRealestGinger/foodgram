import hashlib

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.utils import LimitPagination
from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from .utils import RecipeFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

    def get_queryset(self):
        return self.queryset.order_by('name')


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_fields = {
        'name': ['istartswith'],
    }
    pagination_class = None

    def get_queryset(self):
        return self.queryset.order_by('name')


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPagination
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeSerializer

    def get_queryset(self):
        return self.queryset.order_by('-published_at')

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = self.get_object()
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
            if not favorite:
                return Response(
                    {'errors': 'Рецепт не в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = self.get_object()
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            cart = ShoppingCart.objects.filter(user=user, recipe=recipe).first()
            if not cart:
                return Response(
                    {'errors': 'Рецепта нет в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        recipes = Recipe.objects.filter(shopping_cart__user=user)
        ingredients = {}
        for recipe in recipes:
            for ing in IngredientInRecipe.objects.filter(recipe=recipe):
                key = (ing.ingredient.name, ing.ingredient.measurement_unit)
                ingredients.setdefault(key, 0)
                ingredients[key] += ing.amount
        lines = []
        for (name, unit), amount in ingredients.items():
            lines.append(f"{name} ({unit}) — {amount}")
        content = "\n".join(lines) if lines else "Список покупок пуст."

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class RecipeShortLinkView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, id):
        try:
            recipe = Recipe.objects.get(pk=id)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Recipe not found.'}, status=404)
        short_hash = hashlib.md5(str(recipe.id).encode()).hexdigest()[:6]
        short_link = f"https://foodgram.example.org/s/{short_hash}"
        return Response({'short-link': short_link})
