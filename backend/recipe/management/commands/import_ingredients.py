from recipe.models import Ingredient
from .base_import_fixture import BaseImportFixtureCommand


class Command(BaseImportFixtureCommand):
    model = Ingredient
