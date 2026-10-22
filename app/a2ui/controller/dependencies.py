from functools import lru_cache

from app.a2ui.service import A2uiGenerationService
from app.a2ui.service.catalog_service import CatalogService
from app.common.config import get_settings


@lru_cache
def get_catalog_service() -> CatalogService:
    return CatalogService()


@lru_cache
def get_generation_service() -> A2uiGenerationService:
    return A2uiGenerationService(get_settings(), get_catalog_service())

