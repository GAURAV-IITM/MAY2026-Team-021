from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.openapi import configure_openapi
from app.core.request_context import REQUEST_ID_HEADER, resolve_request_id
from app.schemas.common import error_responses


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
            {
                "name": "Students",
                "description": "Tenant-scoped student profiles, statuses, and invitations.",
            },
            {
                "name": "Floors",
                "description": "Physical library floor management.",
            },
            {
                "name": "Seats",
                "description": "Physical seat records and operational statuses.",
            },
            {
                "name": "Shifts",
                "description": "Study shift definitions and overlap validation.",
            },
            {
                "name": "Settings",
                "description": "Library profile and operating preferences.",
            },
            {
                "name": "Announcements",
                "description": (
                    "Tenant-scoped owner announcement management and "
                    "lifecycle commands."
                ),
            },
            {
                "name": "Seat requests",
                "description": (
                    "Tenant-scoped owner review of student seat-change "
                    "requests without allocation mutation."
                ),
            },
            {
                "name": "Reports",
                "description": (
                    "Tenant-scoped Owner dashboard and operational reports "
                    "computed from source domain records."
                ),
            },
            {
                "name": "Super admin",
                "description": (
                    "Platform-wide library administration restricted to "
                    "authenticated Super Admin users."
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
        responses=error_responses(500),
        openapi_extra={"x-user-stories": ["SYSTEM-API-DISCOVERY"]},
    )
    def root() -> dict[str, str]:
        return {"message": "Smart Library API"}

    @application.get(
        "/health",
        tags=["System"],
        operation_id="getHealth",
        summary="Check API health",
        responses=error_responses(500),
        openapi_extra={"x-user-stories": ["SYSTEM-HEALTH-CHECK"]},
    )
    def health() -> dict[str, str]:
        return {"status": "ok"}

    configure_openapi(application)
    return application


app = create_app()
