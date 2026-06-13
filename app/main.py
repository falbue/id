from fastapi import FastAPI
from app.database import create_db_and_tables
from app.api import auth, tokens
from fastapi.middleware.cors import CORSMiddleware
from config import config

app = FastAPI(
    title="Auth Microservice",
    description="Сервис авторизации на FastAPI + SQLModel",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ваш фронтенд или "*" для тестов
    allow_credentials=True,  # ВАЖНО: разрешить отправку куки!
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(auth.router, prefix=config.PREFIX_AUTH)
app.include_router(tokens.router, prefix=config.PREFIX_TOKENS)
