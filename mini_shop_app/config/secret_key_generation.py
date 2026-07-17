import secrets

# token_urlsafe генерирует строку, безопасную для URL и заголовков
# Число 64 — это количество байт. На выходе строка будет длиннее (около 86 символов).
new_secret_key = secrets.token_urlsafe(64)

print("Ваш новый SECRET_KEY:")
print(new_secret_key)