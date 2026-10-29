from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import get_async_session

Session = Annotated[AsyncSession, Depends(get_async_session)]


class PaginationParams:
    def __init__(
        self,
        offset: int = Query(
            default=0,
            ge=0,
            description="Смещение для пагинации",
        ),
        limit: int = Query(
            default=100,
            ge=1,
            le=1000,
            description="Количество записей на странице",
        ),
    ):
        self.offset = offset
        self.limit = limit


Pagination = Annotated[PaginationParams, Depends(PaginationParams)]
