from collections import Counter

from django.contrib import admin
from django.core.exceptions import ValidationError
import django_filters

from recipe.models import Recipe, Ingredient, IngredientInRecipe


def create_ingredients(recipe, ingredients_data):
    IngredientInRecipe.objects.bulk_create([
        IngredientInRecipe(
            recipe=recipe,
            ingredient_id=ingredient['id'],
            amount=ingredient['amount']
        )
        for ingredient in ingredients_data
    ])


def check_duplicates(items, field_name):
    ids = [item['id'] if isinstance(item, dict) else item.id for item in items]
    if len(ids) != len(set(ids)):
        duplicates = [
            item
            for item, count in Counter(ids).items()
            if count > 1
        ]
        raise ValidationError(
            {
                field_name: (
                    (
                        f'{field_name.capitalize()} не должны повторяться. '
                        f'Дубли: {duplicates}'
                    )
                )
            }
        )


def is_related(self, obj, relation):
    user = self.context['request'].user
    if user.is_anonymous:
        return False
    return getattr(obj, relation).filter(user=user).exists()


class CookingTimeListFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_bin'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        times = list(qs.values_list('cooking_time', flat=True))
        if not times:
            return []
        times_sorted = sorted(times)
        n = len(times_sorted)
        N_idx = n // 3
        M_idx = 2 * n // 3
        N = times_sorted[N_idx] if n > 0 else 0
        M = times_sorted[M_idx] if n > 0 else 0

        fast_count = sum(t <= N for t in times)
        medium_count = sum(N < t <= M for t in times)
        slow_count = sum(t > M for t in times)

        return [
            ('fast', f'быстрее {N} мин ({fast_count})'),
            ('medium', f'быстрее {M} мин ({medium_count})'),
            ('slow', f'долго ({slow_count})'),
        ]

    def queryset(self, request, recipes_queryset):
        times = list(recipes_queryset.values_list('cooking_time', flat=True))
        if not times:
            return recipes_queryset
        times_sorted = sorted(times)
        n = len(times_sorted)
        N_idx = n // 3
        M_idx = 2 * n // 3
        N = times_sorted[N_idx] if n > 0 else 0
        M = times_sorted[M_idx] if n > 0 else 0

        if self.value() == 'fast':
            return recipes_queryset.filter(cooking_time__lte=N)
        if self.value() == 'medium':
            return recipes_queryset.filter(
                cooking_time__gt=N,
                cooking_time__lte=M
            )
        if self.value() == 'slow':
            return recipes_queryset.filter(cooking_time__gt=M)
        return recipes_queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = django_filters.NumberFilter(field_name='author')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author']

    def filter_is_favorited(self, recipes, name, value):
        user = self.request.user
        if not value:
            return recipes
        if not user.is_authenticated:
            return recipes.none()
        return recipes.filter(favorites__user=user)

    def filter_is_in_shopping_cart(self, recipes, name, value):
        user = self.request.user
        if not value:
            return recipes
        if not user.is_authenticated:
            return recipes.none()
        return recipes.filter(shopping_carts__user=user)
