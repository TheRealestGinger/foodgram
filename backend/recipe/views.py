from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError

from .models import Recipe


def short_link_redirect(request, recipe_id):
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise ValidationError(f'Рецепт с id {recipe_id} не найден.')
    return redirect(f'recipes/{recipe_id}/')
