# Что это

Микросервис аутентификации на FastAPI и SQLModel. Реализует вход, регистрацию и управление сессиями через JWT токены

## Стек

*   FastAPI
*   SQLModel (SQLAlchemy)
*   JWT (PyJWT)
*   Passlib (bcrypt)

## Запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Фал .env создаётся при первом запуске

3. Запустите сервер:
```bash
uvicorn app.main:app --reload
```

Документация API доступна по адресу: `http://localhost:8000/docs`

## Основные эндпоинты

*   `POST /auth/registration` — Регистрация
*   `POST /auth/login` — Вход
*   `POST /auth/refresh` — Обновление токена (использует куки)
*   `POST /auth/logout` — Выход
*   `GET /tokens/` — Список активных сессий
*   `DELETE /tokens/{id}` — Отозвать конкретный токен
*   `DELETE /tokens/all` — Выйти со всех устройств

## Тестирование

Для тестов можно использовать Bruno или Postman.
*   При вызове `/auth/login` сохраните `access_token` из ответа.
*   Для защищенных запросов добавляйте заголовок: `Authorization: Bearer <token>`.
*   Refresh токен отправляется браузером/клиентом автоматически в куках.