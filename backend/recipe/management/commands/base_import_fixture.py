import json

from django.core.management.base import BaseCommand


class BaseImportFixtureCommand(BaseCommand):
    model = None
    fixture_path = None
    help = 'Импорт данных из JSON-фикстуры'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_path',
            type=str,
            help='Путь к JSON-фикстуре'
        )

    def handle(self, *args, **options):
        json_path = options['json_path']
        try:
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)
            objects = []
            for obj in data:
                fields = obj.get('fields', {})
                objects.append(self.model(**fields))
            self.model.objects.bulk_create(objects, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'Импортировано {len(objects)} объектов модели {self.model.__name__}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка импорта: {e}'))
