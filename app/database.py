from sqlmodel import create_engine, SQLModel
from app.config import config as settings
import psycopg2
from urllib.parse import urlparse


def ensure_database_exists():
    """Создает базу данных, если она не существует"""
    parsed = urlparse(settings.DATABASE_URL)

    default_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"

    try:
        conn = psycopg2.connect(default_url)
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{parsed.path[1:]}'")
        exists = cursor.fetchone()

        if not exists:
            print(f"Creating database {parsed.path[1:]}...")
            cursor.execute(f'CREATE DATABASE "{parsed.path[1:]}"')
            print("Database created successfully!")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        raise


engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)


def create_db_and_tables():
    ensure_database_exists()  # Сначала создаем БД
    SQLModel.metadata.create_all(engine)  # Затем создаем таблицы


def get_session():
    from sqlmodel import Session

    with Session(engine) as session:
        yield session
