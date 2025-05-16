from fastapi import APIRouter

from app.api.routes import doc_int

router = APIRouter()

router.include_router(doc_int.router)