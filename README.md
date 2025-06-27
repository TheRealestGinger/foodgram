![Workflow](https://github.com/TheRealestGinger/foodgram/actions/workflows/main.yml/badge.svg?event=push)
# Foodgram

## Описание

**Foodgram** — это онлайн-сервис для публикации, поиска и хранения рецептов.  
Пользователи могут делиться своими рецептами, добавлять их в избранное, формировать список покупок, подписываться на других авторов и искать рецепты по тегам и ингредиентам.

### Основные функции:
- Регистрация и аутентификация пользователей
- Публикация, редактирование и удаление рецептов
- Добавление рецептов в избранное
- Формирование списка покупок
- Подписка на других пользователей
- Поиск и фильтрация рецептов по тегам, автору, названию и ингредиентам
- Админ-зона с расширенным поиском и фильтрацией

---

## Технологический стек

- Python 3.10+
- Django 4.x
- Django REST Framework
- PostgreSQL
- Docker, Docker Compose
- Gunicorn, Nginx
- GitHub Actions (CI/CD)
- React (frontend, если используется)

---

## Как развернуть проект

### 1. Клонируйте репозиторий

```sh
git clone https://github.com/<your-username>/foodgram.git
cd foodgram
```

### 2. Заполните файл `.env`

Создайте файл `.env` в корне проекта и заполните его по примеру ниже:

```
SECRET_KEY='your-django-secret-key'
POSTGRES_DB=django
POSTGRES_USER=django_user
POSTGRES_PASSWORD=your_db_password
DB_HOST=db
DB_PORT=5432
DJANGO_DEBUG=False
HOSTS=your.domain.com,127.0.0.1
USE_SQLITE=False
```

### 3. Убедитесь, что у вас есть папка `data` с файлом ингредиентов (например, `ingredients.json`).

### 4. Соберите и запустите контейнеры

```sh
docker compose -f docker-compose.production.yml up -d
```

### 5. Выполните миграции и соберите статику

```sh
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

### 6. Импортируйте ингредиенты (один раз)

```sh
docker compose -f docker-compose.production.yml exec backend python manage.py loaddata /app/data/ingredients.json
```

### 7. (Опционально) Создайте суперпользователя

```sh
docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

---

## Автор

**TheRealestGinger (Никита Гордейко)**  
GitHub: [https://github.com/TheRealestGinger](https://github.com/TheRealestGinger)

## Домен: cleza.hopto.org