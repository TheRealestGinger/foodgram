from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Recipe
from .serializers import RecipeSerializer


def short_link_redirect(request, recipe_id):
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise ValidationError(f'Рецепт с id {recipe_id} не найден.')
    recipe = Recipe.objects.get(pk=recipe_id)
    serializer = RecipeSerializer(recipe, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
