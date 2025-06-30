import json

from django.core.management.base import BaseCommand


class BaseImportFixtureCommand(BaseCommand):
    model = None
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
                created = self.model.objects.bulk_create(
                    (self.model(**obj) for obj in json.load(f)),
                    ignore_conflicts=True
                )
            self.stdout.write(self.style.SUCCESS(
                f'Импортировано {len(created)} объектов модели '
                f'{self.model.__name__}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка импорта из файла {json_path}: {e}'
            ))
