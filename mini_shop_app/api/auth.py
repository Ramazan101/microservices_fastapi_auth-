from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from mini_shop_app.database.db import SessionLocal
from mini_shop_app.database.models import User, RefreshToken
from mini_shop_app.database.schema import UserRegisterSchema, UserCreate

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime
from mini_shop_app.config.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME
)
from typing import Optional
from jose import jwt, JWTError, ExpiredSignatureError

# Настройка шифрования: используем надежный алгоритм bcrypt для работы с паролями
pwd_context = CryptContext(schemes=["bcrypt"])

# Настройка FastAPI для автоматического поиска Bearer токена в заголовках запросов
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login/")

# Инициализируем роутер для группы эндпоинтов авторизации (/auth)
auth_router = APIRouter(prefix='/auth', tags=['Auth'])


# Зависимость (Dependency) для безопасного открытия и закрытия сессии с базой данных
async def get_db():
    db = SessionLocal()  # Открываем сессию при каждом новом запросе к API
    try:
        yield db  # Передаем сессию в роут
    finally:
        db.close()  # ВСЕГДА принудительно закрываем соединение после окончания работы роута


# Превращаем сырой пароль ("adminadmin") в безопасный хэш для хранения в БД
def get_password_hash(password):
    return pwd_context.hash(password)


# Проверяем, совпадает ли введенный пользователем пароль с хэшем из базы данных
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Генерация короткоживущего Access-токена (обычно на несколько минут/часов)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_LIFETIME)

    to_encode.update({"exp": expire})  # Добавляем время "смерти" токена в payload
    # Шифруем данные с помощью секретного ключа проекта
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# генерация долгоживущего refresh токена
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_LIFETIME))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

### Endpoints

@auth_router.post('/register/', response_model=dict)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя.

    Что делает:
    1. Проверяет уникальность username и email. Если заняты - прерывает запрос.
    2. Хэширует пароль перед сохранением (в БД никогда не хранятся пароли в чистом виде).
    3. Записывает данные в базу.

    Message на выходе:
    Возвращает JSON с подтверждением, чтобы font-end понял, что аккаунт успешно создан,
    и смог, например, показать всплывающее уведомление и перенаправить на страницу логина.
    """
    # Шаг 1: Проверяем, нет ли уже пользователя с таким же username
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(detail='There is an username like this.', status_code=400)

    # Шаг 2: Проверяем, нет ли уже пользователя с таким же email
    email = db.query(User).filter(User.email == user.email).first()
    if email:
        raise HTTPException(detail='There is an email like this.', status_code=400)

    # Шаг 3: Шифруем пароль
    hash_password = get_password_hash(user.password)

    # Шаг 4: Готовим объект для записи в SQLAlchemy модели
    user_data = User(
        username=user.username,
        email=user.email,
        user_name=user.user_name,
        phone_number=user.phone_number,
        role=user.role,
        password_hash=hash_password,
    )

    # Шаг 5: Сохраняем в физическую базу данных
    db.add(user_data)
    db.commit()
    db.refresh(user_data)  # Обновляем объект, чтобы у него появился сгенерированный базой id

    return {'message': 'Your are registered'}


@auth_router.post('/login/', response_model=dict)
async def login(user: UserRegisterSchema, db: Session = Depends(get_db)):
    """
    Вход в систему (Аутентификация).

    Что делает:
    1. Ищет пользователя по username.
    2. Сравнивает отправленный пароль с захэшированным в БД.
    3. Если всё ок - генерирует ПАРУ токенов (Access и Refresh).
    4. Сохраняет Refresh-токен в базу данных, чтобы сессию можно было контролировать или отозвать.

    Message на выходе:
    Возвращает токены и их тип. Frontend должен сохранить их (в localStorage или Cookies).
    Access-токен будет крепиться к каждому запросу для подтверждения личности,
    а Refresh-токен нужен для получения нового Access, когда старый «умрет».
    """
    # Шаг 1: Ищем пользователя
    user_db = db.query(User).filter(User.username == user.username).first()

    # Шаг 2: Проверяем существование и правильность пароля
    if not user_db or not verify_password(user.password, user_db.password_hash):
        raise HTTPException(detail="The information you entered is incorrect.", status_code=401)

    # Шаг 3: Генерируем оба токена. В Payload (sub) зашиваем ID пользователя
    access_token = create_access_token({"sub": str(user_db.id)})
    refresh_token = create_refresh_token({"sub": str(user_db.id)})

    # Шаг 4: Записываем Refresh-токен в базу данных (связываем с этим юзером)
    token_db = RefreshToken(user_id=user_db.id, token=refresh_token)
    db.add(token_db)
    db.commit()

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'Bearer'}


@auth_router.post("/logout/")
async def logout(refresh_token: str, db: Session = Depends(get_db)):
    """
    Выход из аккаунта.

    Что делает:
    Находит переданный Refresh-токен в базе данных и физически его удаляет.

    Message на выходе:
    Сообщение "You logged out" сигнализирует фронтенду, что сессия на бэкенде уничтожена.
    После этого фронтенд должен стереть токены из своей памяти (памяти браузера),
    и пользователь больше не сможет делать авторизованные запросы без нового логина.
    """
    # Ищем токен в базе
    stored = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not stored:
        raise HTTPException(status_code=401, detail="Token not found")

    # Удаляем токен из БД (аннулируем сессию)
    db.delete(stored)
    db.commit()
    return {"message": "You logged out"}


@auth_router.post("/refresh/")
async def refresh_jwt(refresh_token: str, db: Session = Depends(get_db)):
    """
    Обновление Access-токена без повторного ввода логина и пароля.

    Что делает:
    1. Проверяет, существует ли этот Refresh-токен в нашей базе (если мы его удалили при logout, обновиться не получится).
    2. Проверяет валидность токена и не истек ли его срок годности.
    3. Извлекает ID пользователя (sub) из токена.
    4. Выпускает СВЕЖИЙ Access-токен.

    Message на выходе:
    Возвращает новый access_token. Это позволяет пользователю оставаться «залогиненным»
    в приложении незаметно для него самого (fontend делает этот запрос автоматически на заднем плане).
    """
    # Шаг 1: Проверяем, числится ли этот токен в базе активных сессий
    stored = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()

    if not stored:
        raise HTTPException(status_code=401, detail="Token not found")

    # Шаг 2: Расшифровываем токен и проверяем на валидность
    try:
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Шаг 3: Достаем ID пользователя из Payload токена
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Шаг 4: Генерируем новый короткоживущий Access-токен
    access_token = create_access_token({"sub": user_id})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

"""Commits это чисто для того чтобы понять что выполняет определенное поле в коде :)###"""