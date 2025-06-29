from djoser.serializers import UserCreateSerializer
from djoser.views import UserViewSet as DjoserUserViewSet
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AuthorWithRecipesSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserDetailSerializer,
)
from .utils import IngredientFilter, LimitPagination, RecipeFilter
from recipe.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    pagination_class = LimitPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserDetailSerializer
        return UserCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user

        if request.method != 'POST':
            get_object_or_404(
                Subscription,
                user=user,
                author=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if author == user:
            raise ValidationError(
                {'errors': 'Нельзя подписаться на самого себя.'}
            )
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            author=author
        )
        if not created:
            raise ValidationError(
                {
                    'errors': (
                        f'Вы уже подписаны на автора: '
                        f'{author.username}.'
                    )
                }
            )
        return Response(AuthorWithRecipesSerializer(
            subscription.author,
            context={'request': request}
        ).data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = request.user.subscriptions.all()
        authors = [sub.author for sub in subscriptions]
        page = self.paginate_queryset(authors)
        serializer = AuthorWithRecipesSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser, JSONParser]
    )
    def avatar(self, request):
        user = request.user
        if request.method != 'PUT':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = UserAvatarSerializer(
            user,
            data=request.data
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']},
                status=status.HTTP_200_OK
            )


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

    def get_queryset(self):
        return self.queryset.order_by('name')


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_add_remove(self, request, pk, model):
        user = request.user
        if request.method == 'POST':
            recipe = self.get_object()
            obj, created = model.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if not created:
                return Response(
                    {
                        'errors': (
                            f'Рецепт "{recipe.name}" уже добавлен в '
                            f'{model.__name__}.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(model, user=user, recipe__pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self._handle_add_remove(
            request, pk,
            Favorite
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_add_remove(
            request, pk,
            ShoppingCart
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredient_links = IngredientInRecipe.objects.filter(
            recipe__shopping_carts__user=user
        ).select_related('ingredient')

        ingredients = {}
        for ing in ingredient_links:
            key = (ing.ingredient.name, ing.ingredient.measurement_unit)
            ingredients.setdefault(key, 0)
            ingredients[key] += ing.amount
        ingredients = dict(sorted(ingredients.items(), key=lambda x: x[0][0]))
        lines = []
        for (name, unit), amount in ingredients.items():
            lines.append(f'{name} ({unit}) — {amount}')
        content = render_to_string(
            'shopping_cart.txt',
            {
                'date': timezone.now().strftime('%d.%m.%Y'),
                'ingredients': [
                    {
                        'num': i,
                        'name': name.capitalize(),
                        'amount': amount,
                        'unit': unit
                    }
                    for i, ((name, unit), amount) in enumerate(
                        ingredients.items(), start=1
                    )
                ],
                'recipes': [
                    {
                        'name': recipe.name,
                        'author': str(recipe.author)
                    }
                    for recipe in Recipe.objects.filter(
                        shopping_carts__user=user
                    )
                ]
            }
        )

        return FileResponse(
            content,
            as_attachment=True,
            filename='shopping_cart.txt'
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def short_link(self, request, pk=None):
        exists = Recipe.objects.filter(pk=pk).exists()
        if not exists:
            raise ValidationError(
                {'detail': f'Рецепт с id={pk} не найден.'}
            )
        short_link = request.build_absolute_uri(
            reverse('short-recipe', kwargs={'pk': pk})
        )
        return Response({'short-link': short_link})
