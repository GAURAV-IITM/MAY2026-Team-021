from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentTenant, DatabaseSession, require_library_staff
from app.schemas.common import SuccessResponse, error_responses
from app.schemas.payment import MONTH_PATTERN
from app.schemas.report import (
    OwnerDashboardData,
    OwnerReportsData,
    ReportOptionsData,
)
from app.services import report as report_service


router = APIRouter(
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(401, 403, 500),
)


@router.get(
    "/options",
    response_model=SuccessResponse[ReportOptionsData],
    operation_id="getOwnerReportOptions",
    summary="Get Owner report filter options",
    description=(
        "Returns tenant-scoped month, floor, and shift options. The library is "
        "derived from the authenticated Owner or staff membership."
    ),
    openapi_extra={"x-user-stories": ["REPORT-FILTER-OPTIONS"]},
)
def get_report_options(
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[ReportOptionsData]:
    return SuccessResponse(
        message="Report options fetched successfully.",
        data=report_service.get_report_options(
            db,
            tenant.library_id,
            tenant.library.timezone,
        ),
    )


@router.get(
    "",
    response_model=SuccessResponse[OwnerReportsData],
    operation_id="getOwnerReports",
    summary="Get Owner reports",
    description=(
        "Builds tenant-scoped revenue, occupancy, student, and pending-fee "
        "reports from source records. Financial values use completed payment "
        "transactions and occupancy uses active allocation overlap rules."
    ),
    responses=error_responses(404, 422),
    openapi_extra={
        "x-user-stories": [
            "REPORT-REVENUE",
            "REPORT-OCCUPANCY",
            "REPORT-STUDENTS",
            "REPORT-PENDING-FEES",
        ]
    },
)
def get_reports(
    db: DatabaseSession,
    tenant: CurrentTenant,
    start_month: Annotated[
        str | None,
        Query(alias="startMonth", pattern=MONTH_PATTERN),
    ] = None,
    end_month: Annotated[
        str | None,
        Query(alias="endMonth", pattern=MONTH_PATTERN),
    ] = None,
    floor_id: Annotated[
        uuid.UUID | None,
        Query(alias="floorId"),
    ] = None,
    shift_id: Annotated[
        uuid.UUID | None,
        Query(alias="shiftId"),
    ] = None,
) -> SuccessResponse[OwnerReportsData]:
    reports = report_service.get_reports(
        db,
        tenant.library_id,
        tenant.library.timezone,
        start_month=start_month,
        end_month=end_month,
        floor_id=floor_id,
        shift_id=shift_id,
    )
    return SuccessResponse(
        message="Reports fetched successfully.",
        data=reports,
    )


@router.get(
    "/dashboard",
    response_model=SuccessResponse[OwnerDashboardData],
    operation_id="getOwnerOperationalDashboard",
    summary="Get Owner operational dashboard",
    description=(
        "Returns tenant-scoped operational metrics. Occupancy defaults to the "
        "current library-local date and finance defaults to that billing month."
    ),
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["OWNER-OPERATIONAL-DASHBOARD"]},
)
def get_dashboard(
    db: DatabaseSession,
    tenant: CurrentTenant,
    report_date: Annotated[date | None, Query(alias="date")] = None,
    billing_month: Annotated[
        str | None,
        Query(alias="billingMonth", pattern=MONTH_PATTERN),
    ] = None,
) -> SuccessResponse[OwnerDashboardData]:
    dashboard = report_service.get_dashboard(
        db,
        tenant.library_id,
        tenant.library.timezone,
        report_date=report_date,
        billing_month=billing_month,
    )
    return SuccessResponse(
        message="Dashboard summary fetched successfully.",
        data=dashboard,
    )
