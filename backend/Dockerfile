FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

# Копируем скрипт ожидания базы
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Используем wait-for-it для ожидания готовности базы
CMD ["/wait-for-it.sh", "db:5432", "--", "gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]