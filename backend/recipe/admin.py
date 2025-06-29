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
from api.utils import CookingTimeListFilter


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
        items = [f"{i.ingredient.name} ({i.amount})" for i in ingredients]
        return '<br>'.join(items)

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

    @admin.display(description='Число рецептов')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name', 'slug')
    list_display = (
        [field.name for field in Tag._meta.fields]
        + ['recipes_count']
    )

    @admin.display(description='Число рецептов')
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

    @mark_safe
    def avatar_tag(self, user):
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" width="50" height="50" '
                'style="object-fit:cover;border-radius:50%;">'
            )
        return '-'
    avatar_tag.short_description = 'Аватар'

    @admin.display(description='Рецептов')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.subscribers.count()
