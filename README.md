Проект: МедиаЦентр Первых | Ейский район

Как проверить локально:
1. Скопируйте этот архив и распакуйте.
2. Положите ваш логотип в static/img/ под именем logo_pervye.png
3. Создайте виртуальное окружение и установите зависимости:
    python -m venv venv
    source venv/bin/activate  # или venv\Scripts\activate на Windows
    pip install -r requirements.txt
4. Создайте .env по примеру .env.example (укажите SECRET_KEY).
5. Запустите приложение:
    python app.py
6. Откройте http://localhost:5000

Примечание: база SQLite создаётся автоматически в файле mediacenter.db.
Telegram webhook работает только если у приложения есть публичный URL (ngrok/Render/etc.) и вы установите webhook.
