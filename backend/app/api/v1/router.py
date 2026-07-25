from fastapi import APIRouter

from app.api.v1.endpoints import (
    allocations,
    announcements,
    auth,
    floors,
    libraries,
    payments,
    reports,
    seats,
    settings,
    shifts,
    students,
    super_admin,
)


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(libraries.router, prefix="/libraries", tags=["Libraries"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(floors.router, prefix="/floors", tags=["Floors"])
api_router.include_router(seats.router, prefix="/seats", tags=["Seats"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["Shifts"])
api_router.include_router(allocations.router, prefix="/seat-allocations", tags=["Seat allocations"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(announcements.router, prefix="/announcements", tags=["Announcements"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(super_admin.router, prefix="/platform", tags=["Super admin"])
