from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    SerializerMethodField,
)

from core.utils import Base64ImageField
from recipe.models import Ingredient, IngredientInRecipe, Recipe, Tag, User
from .utils import check_duplicates, is_related


COOKING_TIME_MIN_VALUE = 1
INGREDIENT_AMOUNT_MIN_VALUE = 1


class UserDetailSerializer(DjoserUserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed'
        )
        read_only_fields = fields

    def get_is_subscribed(self, user_instance):
        user = self.context.get('request').user
        return (
            not user.is_anonymous
            and user_instance.subscriptions_of_authors.filter(
                user=user
            ).exists()
        )


class AuthorWithRecipesSerializer(UserDetailSerializer):
    recipes = SerializerMethodField()
    recipes_count = IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar',
            'recipes', 'recipes_count',
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit', 10**10)
        recipes = Recipe.objects.filter(author=obj)[:int(limit)]
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class UserAvatarSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeReadSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class IngredientInRecipeWriteSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = IntegerField(min_value=INGREDIENT_AMOUNT_MIN_VALUE)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'cooking_time',
            'tags', 'ingredients'
        )
        extra_kwargs = {
            'cooking_time': {'min_value': COOKING_TIME_MIN_VALUE}
        }

    def create_ingredients(recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create(
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Нужно указать хотя бы один продукт.'}
            )
        if not tags:
            raise ValidationError({'tags': 'Нужно указать хотя бы один тег.'})

        check_duplicates(ingredients, 'ingredients')
        check_duplicates(tags, 'tags')

        return data


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients'
    )
    author = UserDetailSerializer()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'cooking_time',
            'tags', 'ingredients', 'author',
            'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        return is_related(self, obj, 'favorites')

    def get_is_in_shopping_cart(self, obj):
        return is_related(self, obj, 'shopping_carts')


class RecipeMinifiedSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields
