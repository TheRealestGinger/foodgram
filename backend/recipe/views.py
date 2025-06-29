from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Recipe


class ShortLinkRedirectView(APIView):
    def get(self, request, short_hash):
        pk = int(short_hash, 36)
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response({'id': recipe.pk, 'name': recipe.name})
