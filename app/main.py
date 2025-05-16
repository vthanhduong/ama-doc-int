from fastapi import FastAPI
from app.core.config import settings
from app.api.main import router

app = FastAPI(
    title=settings.APP_NAME
)

app.include_router(
    router=router,
    prefix=settings.API_VERSION,
)
