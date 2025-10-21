# Используем стабильный Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы проекта
COPY . .

# Обновляем pip и ставим зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]
