from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.openapi import configure_openapi
from app.core.request_context import REQUEST_ID_HEADER, resolve_request_id


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        openapi_tags=[
            {
                "name": "System",
                "description": "API discovery and health endpoints.",
            },
            {
                "name": "Authentication",
                "description": (
                    "Library registration, JWT sessions, current-user access, "
                    "and account security."
                ),
            },
        ],
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )
    register_exception_handlers(application)
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.middleware("http")
    async def add_request_context(request, call_next):
        request.state.request_id = resolve_request_id(request)
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request.state.request_id
        return response

    @application.get(
        "/",
        tags=["System"],
        operation_id="getApiRoot",
        summary="Get API information",
    )
    def root() -> dict[str, str]:
        return {"message": "Smart Library API"}

    @application.get(
        "/health",
        tags=["System"],
        operation_id="getHealth",
        summary="Check API health",
    )
    def health() -> dict[str, str]:
        return {"status": "ok"}

    configure_openapi(application)
    return application


app = create_app()
