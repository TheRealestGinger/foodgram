from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


COOKING_TIME_MIN_VALUE = 1
INGREDIENT_AMOUNT_MIN_VALUE = 1


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        null=False
    )
    avatar = models.ImageField(upload_to='users/', blank=True, null=True)
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=(
                    'Username may contain only letters, digits and '
                    '@/./+/-/_ characters.'
                )
            )
        ],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='subscriptions_of_authors',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название продукта'
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_measurement_unit'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField(max_length=256, verbose_name='Название рецепта')
    image = models.ImageField(upload_to='recipes/', verbose_name='Изображение')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (минуты)',
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN_VALUE,
                message=(
                    f'Время приготовления должно быть больше '
                    f'{COOKING_TIME_MIN_VALUE - 1}'
                )
            )
        ]
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты'
    )

    published_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        ordering = ('-published_at',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                INGREDIENT_AMOUNT_MIN_VALUE,
                message=(
                    f'Количество продукта должно быть больше '
                    f'{INGREDIENT_AMOUNT_MIN_VALUE - 1}'
                )
            )
        ]
    )

    class Meta:
        ordering = ('ingredient',)
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Продукт рецепта'
        verbose_name_plural = 'Продукты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient.name} в {self.recipe.name}'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Favorite(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_favorite'
            )
        ]


class ShoppingCart(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        default_related_name = 'shopping_carts'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_shopping_cart'
            )
        ]
