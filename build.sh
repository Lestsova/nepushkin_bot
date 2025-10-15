#!/usr/bin/env bash
set -o errexit

echo "🔧 Устанавливаем зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🚀 Запускаем бота..."
python bot.py
