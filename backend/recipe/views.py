from django.shortcuts import redirect
from rest_framework.response import Response

from .models import Recipe


def short_link_redirect(request, recipe_id):
    exists = Recipe.objects.filter(pk=recipe_id).exists()
    if not exists:
        return Response(
            {'detail': f'Рецепт с id {recipe_id} не найден.'},
            status=404
        )
    return redirect(f'/recipes/{recipe_id}/')
