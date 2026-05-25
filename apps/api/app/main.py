from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="TradeOffLab API",
        version="0.1.0",
        description="Structured decision engineering API for TradeOffLab.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {
            "name": "TradeOffLab API",
            "status": "ok",
            "default_model": settings.litellm_model,
        }

    app.include_router(router, prefix="/api")
    return app


app = create_app()

