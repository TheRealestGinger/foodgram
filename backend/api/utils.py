from collections import Counter

from django.core.exceptions import ValidationError
import django_filters
from rest_framework.pagination import PageNumberPagination

from recipe.models import Recipe, Ingredient


def check_duplicates(items, field_name):
    def get_id(item):
        if isinstance(item, dict):
            return item.get('id') or item.get('ingredient')
        if hasattr(item, 'id'):
            return item.id
        return item
    ids = [get_id(item) for item in items]
    if len(ids) == len(set(ids)):
        return
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


class LimitPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


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
        return recipes.filter(favorite__user=user)

    def filter_is_in_shopping_cart(self, recipes, name, value):
        user = self.request.user
        if not value:
            return recipes
        if not user.is_authenticated:
            return recipes.none()
        return recipes.filter(shoppingcart__user=user)
