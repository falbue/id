from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from app import config, setup_logger
from app.routers import auth
from app.services.database import create_db_and_tables

log = setup_logger("APP")

app = FastAPI(
    title="id",
    description="",
    version="development",
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


app.include_router(auth.router, prefix=f"{config.PREFIX_AUTH}", tags=["Аутентификация"])
