from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.files.base import ContentFile
from django.http import FileResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from djoser.serializers import SetPasswordSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.utils import LimitPagination
from recipe.models import (
    User,
    Subscription,
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from .permissions import IsAuthorOrReadOnly
from .utils import RecipeFilter, IngredientFilter
from .serializers import (
    UserSerializer,
    AuthorWithRecipesSerializer,
    UserAvatarSerializer,
    UserDetailSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    pagination_class = LimitPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserDetailSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['post'],
        url_path='set_password',
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(
            serializer.validated_data['new_password']
        )
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
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
                            f'{author.get_full_name() or author.username}.'
                        )
                    }
                )
            return Response(AuthorWithRecipesSerializer(
                subscription.author,
                context={'request': request}
            ).data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(
            user=user,
            author=author
        ).first()
        if not subscription:
            return Response(
                {'errors': 'Подписка не найдена.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(
            user=request.user
        ).order_by('id')
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
        if request.method == 'PUT':
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
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    def _handle_add_remove(
        self, request, pk, model, error_exists, error_not_exists,
        serializer_class=None
    ):
        user = request.user
        recipe = self.get_object()
        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': error_exists},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            if serializer_class:
                serializer = serializer_class(
                    recipe,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(status=status.HTTP_201_CREATED)
        obj = model.objects.filter(user=user, recipe=recipe).first()
        if not obj:
            return Response(
                {'errors': error_not_exists},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.delete()
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
            Favorite,
            f'Рецепт "{self.get_object().name}" уже в избранном.',
            'Рецепта нет в избранном.',
            RecipeMinifiedSerializer
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
            ShoppingCart,
            'Рецепт уже в корзине.',
            'Рецепта нет в корзине.',
            RecipeMinifiedSerializer
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
                        'num': i + 1,
                        'name': name.capitalize(),
                        'amount': amount,
                        'unit': unit
                    }
                    for i, ((name, unit), amount) in enumerate(
                        ingredients.items()
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

        response = HttpResponse(content, content_type='text/plain')
        file = ContentFile(content.encode('utf-8'), name='shopping_cart.txt')
        response = FileResponse(
            file,
            as_attachment=True,
            filename='shopping_cart.txt'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def short_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(f'/r/{recipe.pk}/')
        return Response({'short-link': short_link})
