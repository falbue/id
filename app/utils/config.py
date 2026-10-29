import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорировать лишние переменные
    )

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/auth",
        description="Путь к базе данных",
    )

    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production",
        description="Секретный ключ",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        description="Жизнь токена в минутах",
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30,
        description="Жизнь рефреш токена днях",
    )

    SECURE_COOKIES: bool = Field(
        default=True,
        description="Включить в продакшене с HTTPS",
    )

    COOKIE_DOMAIN: str | None = Field(
        default=None,
        description="Для кросс-доменных куки",
    )

    PREFIX_AUTH: str = Field(
        default="/api/auth",
        description="Перфикс для роутов авторизации",
    )

    PREFIX_TOKENS: str = Field(
        default="/api/tokens",
        description="Перфикс для роутов c токенами",
    )


IN_DOCKER = os.getenv("IN_DOCKER", "").lower() in ("1", "true", "yes")
env_path = Path(".env")

if not IN_DOCKER and not env_path.exists():
    with open(env_path, "w", encoding="utf-8") as f:
        for field_name, field_info in ConfigSettings.model_fields.items():
            desc = field_info.description or ""
            default = field_info.get_default()
            if isinstance(default, bool):
                default = "true" if default else "false"
            else:
                default = str(default)

            f.write(f"# {desc}\n")
            f.write(f"{field_name}={default}\n\n")

    raise RuntimeError(
        "Файл .env не найден и был создан со шаблоном.\n"
        "Отредактируйте параметры перед запуском:\n"
        f"- Файл: {env_path.absolute()}"
    )

config = ConfigSettings()
