from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    Serializer,
    SerializerMethodField,
)

from core.utils import Base64ImageField
from .models import Ingredient, IngredientInRecipe, Recipe, Tag


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


class IngredientInRecipeWriteSerializer(Serializer):
    id = IntegerField()
    amount = IntegerField()


class RecipeWriteSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)
    author = ReadOnlyField(source='author.id')

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'cooking_time',
            'tags', 'ingredients', 'author'
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        validated_data.pop('author', None)
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient in ingredients_data:
                IngredientInRecipe.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount']
                )
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Нужно указать хотя бы один ингредиент.'}
            )
        if not tags:
            raise ValidationError({'tags': 'Нужно указать хотя бы один тег.'})

        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise ValidationError({'tags': 'Теги не должны повторяться.'})

        existing_ingredients = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                'id', flat=True
            )
        )
        missing_ingredients = set(ingredient_ids) - existing_ingredients
        if missing_ingredients:
            raise ValidationError(
                {
                    'ingredients': (
                        f'Ингредиенты с id {list(missing_ingredients)} '
                        'не существуют.'
                    )
                }
            )

        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise ValidationError(
                    {
                        'ingredients': (
                            'Количество ингредиента должно быть больше 0.'
                        )
                    }
                )

        return data


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients'
    )
    image = SerializerMethodField()
    author = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'cooking_time',
            'tags', 'ingredients', 'author',
            'is_favorited', 'is_in_shopping_cart'
        )

    def get_author(self, obj):
        serializer_path = (
            getattr(settings, 'DJOSER', {})
            .get('SERIALIZERS', {})
            .get('user', 'users.serializers.UserDetailSerializer')
        )
        UserDetailSerializer = import_string(serializer_path)
        return UserDetailSerializer(obj.author, context=self.context).data

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return ""

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.shopping_cart.filter(user=user).exists()


class RecipeMinifiedSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
