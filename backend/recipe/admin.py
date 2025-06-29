from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe

from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
    User,
)


class CookingTimeListFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        times = list(qs.values_list('cooking_time', flat=True))
        if len(set(times)) < 3:
            return []
        times_sorted = sorted(times)
        times_count = len(times_sorted)
        first_threshold_index = times_count // 3
        second_threshold_index = 2 * times_count // 3
        first_threshold = times_sorted[first_threshold_index]
        second_threshold = (
            times_sorted[second_threshold_index]
            if times_count > 0 else 0
        )

        fast_recipes_count = sum(
            cooking_time <= first_threshold for cooking_time in times
        )
        medium_recipes_count = sum(
            first_threshold < cooking_time <= second_threshold
            for cooking_time in times
        )
        slow_recipes_count = sum(
            cooking_time > second_threshold for cooking_time in times
        )

        return [
            (
                'fast',
                f'быстрее {first_threshold} мин ({fast_recipes_count})'
            ),
            (
                'medium',
                f'быстрее {second_threshold} мин ({medium_recipes_count})'
            ),
            (
                'slow',
                f'долго ({slow_recipes_count})'
            ),
        ]

    def queryset(self, request, recipes):
        first_threshold = getattr(self, 'first_threshold', 0)
        second_threshold = getattr(self, 'second_threshold', 0)

        if self.value() == 'fast':
            return recipes.filter(cooking_time__lte=first_threshold)
        if self.value() == 'medium':
            return recipes.filter(
                cooking_time__gt=first_threshold,
                cooking_time__lte=second_threshold
            )
        if self.value() == 'slow':
            return recipes.filter(cooking_time__gt=second_threshold)
        return recipes


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags', 'author', CookingTimeListFilter)
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'favorites_count',
        'ingredients_list',
        'image_tag',
    )

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_list(self, recipe):
        ingredients = (
            recipe.ingredientsinrecipe_set.select_related('ingredient')
        )
        return '<br>'.join(
            f"{i.ingredient.name} ({i.amount} {i.ingredient.measurement_unit})"
            for i in ingredients
        )

    @admin.display(description='Картинка')
    @mark_safe
    def image_tag(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" '
                f'style="max-height: 60px; max-width: 60px;" />'
            )
        return '-'

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name', 'measurement_unit')
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    list_filter = ('measurement_unit',)

    @admin.display(description='Рецептов')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name', 'slug')
    list_display = (
        'id',
        'name',
        'color',
        'slug',
        'recipes_count',
    )

    @admin.display(description='Рецептов')
    def recipes_count(self, tag):
        return tag.recipes.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    search_fields = ('username', 'email')
    list_display = (
        'id', 'username', 'full_name', 'email', 'avatar_tag',
        'recipes_count', 'subscriptions_count', 'subscribers_count',
    )
    readonly_fields = ('avatar_tag',)
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('avatar',)}),
    )

    @admin.display(description='ФИ')
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}"

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_tag(self, user):
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" width="50" height="50" '
                'style="object-fit:cover;border-radius:50%;">'
            )
        return '-'

    @admin.display(description='Рецептов')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.subscribers.count()
