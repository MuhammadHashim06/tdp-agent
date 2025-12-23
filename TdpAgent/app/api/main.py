from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.cases import router as cases_router
from app.api.drafts import router as drafts_router
from app.api.emails import router as emails_router
from app.api.attachments import router as attachments_router
from app.api.notification import router as notifications_router

def create_app() -> FastAPI:
    app = FastAPI(title=os.getenv("APP_NAME", "TdpAgent"))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"ok": True}

    app.include_router(cases_router, prefix="/api/cases", tags=["cases"])
    app.include_router(drafts_router, prefix="/api/drafts", tags=["drafts"])
    app.include_router(emails_router, prefix="/api/emails", tags=["emails"])
    app.include_router(attachments_router, prefix="/api/attachments", tags=["attachments"])
    app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])
    return app

app = create_app()
