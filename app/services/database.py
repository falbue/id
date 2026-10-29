from urllib.parse import unquote, urlparse

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app import setup_logger
from app.utils import config

log = setup_logger("DATABASE")


def ensure_database_exists():
    """Создание базы данных, если она не существует"""
    parsed = urlparse(config.DATABASE_URL)
    log.debug(f"Проверка существования базы данных {config.DATABASE_URL}...")

    auth = ""
    if parsed.username:
        auth += unquote(parsed.username)
        if parsed.password:
            auth += f":{unquote(parsed.password)}"
        auth += "@"

    default_url = f"postgresql://{auth}{parsed.hostname}"
    if parsed.port:
        default_url += f":{parsed.port}"
    default_url += "/postgres"

    try:
        conn = psycopg2.connect(default_url)
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{parsed.path[1:]}'")
        exists = cursor.fetchone()

        if not exists:
            log.debug(f"Создание базы данных {parsed.path[1:]}...")
            cursor.execute(f'CREATE DATABASE "{parsed.path[1:]}"')
            log.debug("База данных создана")

        cursor.close()
        conn.close()
    except Exception as e:
        log.error(f"Ошибка проверки/создания базы данных: {e}")
        raise


def get_async_url() -> str:
    """Преобразует URL в формат для asyncpg"""
    url = config.DATABASE_URL
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    elif url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url


def get_sync_url() -> str:
    """Преобразует URL в формат для psycopg2"""
    url = config.DATABASE_URL
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "")
    elif "+psycopg2" in url:
        return url.replace("+psycopg2", "")
    return url


async_engine = create_async_engine(get_async_url(), echo=False, pool_pre_ping=True)

async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


def create_db_and_tables():
    ensure_database_exists()
    sync_engine = create_engine(get_sync_url())
    SQLModel.metadata.create_all(sync_engine)


async def get_async_session():
    async with async_session_maker() as session:
        yield session
