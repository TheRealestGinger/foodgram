from recipe.models import Tag
from .base_import_fixture import BaseImportFixtureCommand


class Command(BaseImportFixtureCommand):
    model = Tag
