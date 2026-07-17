# Микросервис авторизации на FastAPI

Микросервис для регистрации и аутентификации пользователей, построенный на базе FastAPI с использованием JSON Web Tokens (JWT), ORM SQLAlchemy 2.0 и миграций Alembic.

## Основные возможности (Features)

* **Регистрация пользователей**: Проверка уникальности username/email, безопасное хэширование паролей.
* **JWT Аутентификация**: Выдача пары токенов — короткоживущего `access_token` (для запросов) и долгоживущего `refresh_token` (для обновления сессии).
* **Управление сессиями**: Сохранение refresh-токенов в базу данных, что позволяет безопасно выходить из системы (`logout`) и аннулировать старые сессии.
* **Контроль базы данных**: Использование SQLAlchemy 2.0 (SQLite) и автоматическое отслеживание изменений через Alembic.

## Стек технологий

* **Фреймворк**: FastAPI
* **ORM**: SQLAlchemy 2.0
* **База данных**: SQLite
* **Миграции**: Alembic
* **Безопасность**: Passlib (bcrypt), python-jose

## Инструкция по установке и запуску

Выполните следующие шаги для локального запуска микросервиса:

### 1. Клонируйте репозиторий
```bash
git clone git@github.com:Ramazan101/microservices_fastapi_auth-.git
cd microservices_fastapi_auth-
2. Создайте и активируйте виртуальное окружение
Bash
python -m venv .venv
# Для Windows (PowerShell):
.venv\Scripts\activate
3. Установите зависимости
Bash
pip install -r req.txt
4. Настройка переменных окружения
Создайте файл .env внутри папки mini_shop_app/ и добавьте настройки безопасности:

Фрагмент кода
SECRET_KEY=ваш_секретный_ключ_генерации_jwt
ALGORITHM=HS256
ACCESS_TOKEN_LIFETIME=30
REFRESH_TOKEN_LIFETIME=7
5. Примените миграции базы данных
Создайте таблицы в SQLite:

Bash
python -m alembic -c mini_shop_app/alembic.ini upgrade head
6. Запустите сервер
Bash
python main.py
Приложение будет доступно по адресу: http://127.0.0.1:8000.

Интерактивная документация (Swagger UI) доступна по адресу: http://127.0.0.1:8000/docs.
