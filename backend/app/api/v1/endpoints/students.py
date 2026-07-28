"""Tenant-scoped student management endpoints."""
from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
    CurrentStudent,
)
from app.models.enums import StudentStatus
from app.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    PaginationMeta,
    SuccessResponse,
    error_responses,
)
from app.schemas.student import (
    StudentCreate,
    StudentInvitationResponse,
    StudentResponse,
    StudentStatusUpdate,
    StudentUpdate,
    StudentSelfUpdate,
)
from app.services import student as student_service
from app.services.audit import AuditContext


router = APIRouter(
    responses=error_responses(401, 403, 500),
)


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get(
    "/me",
    response_model=SuccessResponse[StudentResponse],
    operation_id="getStudentProfile",
    summary="Get own profile",
    description="Returns the authenticated student's own profile.",
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["STUDENT-PORTAL-PROFILE-VIEW"]},
)
def get_own_profile(
    db: DatabaseSession,
    student_ctx: CurrentStudent,
) -> SuccessResponse[StudentResponse]:
    student_detail = student_service._student_response(db, student_ctx.student)
    return SuccessResponse(
        message="Profile fetched successfully.",
        data=student_detail,
    )


@router.patch(
    "/me",
    response_model=SuccessResponse[StudentResponse],
    operation_id="updateStudentProfile",
    summary="Update own profile",
    description="Allows the authenticated student to update contact and personal fields.",
    responses=error_responses(404, 422),
    openapi_extra={"x-user-stories": ["STUDENT-PORTAL-PROFILE-UPDATE"]},
)
def update_own_profile(
    payload: StudentSelfUpdate,
    request: Request,
    db: DatabaseSession,
    student_ctx: CurrentStudent,
) -> SuccessResponse[StudentResponse]:
    updated = student_service.update_student_profile(
        db,
        student_ctx.library_id,
        student_ctx.student_id,
        payload,
        student_ctx.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Profile updated successfully.",
        data=updated,
    )


@router.get(
    "",
    response_model=PaginatedResponse[StudentResponse],
    operation_id="listStudents",
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["STUDENT-LIST"]},
)
def list_students(
    db: DatabaseSession,
    tenant: CurrentTenant,
    pagination: Pagination,
    student_status: Annotated[
        StudentStatus | None,
        Query(alias="status"),
    ] = None,
) -> PaginatedResponse[StudentResponse]:
    students, total = student_service.list_students(
        db,
        tenant.library_id,
        pagination,
        status=student_status,
    )
    return PaginatedResponse(
        message="Students fetched successfully.",
        data=students,
        meta=PaginationMeta(
            page=pagination.page,
            pageSize=pagination.page_size,
            totalItems=total,
            totalPages=math.ceil(total / pagination.page_size) if total else 0,
        ),
    )


@router.post(
    "",
    response_model=SuccessResponse[StudentResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="createStudent",
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(409, 422),
    openapi_extra={"x-user-stories": ["STUDENT-CREATE"]},
)
def create_student(
    payload: StudentCreate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[StudentResponse]:
    student = student_service.create_student(
        db,
        tenant.library_id,
        tenant.user.id,
        payload,
    )
    return SuccessResponse(
        message="Student created successfully.",
        data=student,
    )


@router.get(
    "/{student_id}",
    response_model=SuccessResponse[StudentResponse],
    operation_id="getStudent",
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["STUDENT-DETAIL"]},
)
def get_student(
    student_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[StudentResponse]:
    return SuccessResponse(
        message="Student fetched successfully.",
        data=student_service.get_student(db, tenant.library_id, student_id),
    )


@router.patch(
    "/{student_id}",
    response_model=SuccessResponse[StudentResponse],
    operation_id="updateStudent",
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["STUDENT-UPDATE"]},
)
def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[StudentResponse]:
    return SuccessResponse(
        message="Student updated successfully.",
        data=student_service.update_student(
            db,
            tenant.library_id,
            student_id,
            payload,
            tenant.user.id,
        ),
    )


@router.patch(
    "/{student_id}/status",
    response_model=SuccessResponse[StudentResponse],
    operation_id="changeStudentStatus",
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(404, 422),
    openapi_extra={"x-user-stories": ["STUDENT-STATUS"]},
)
def change_student_status(
    student_id: uuid.UUID,
    payload: StudentStatusUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[StudentResponse]:
    return SuccessResponse(
        message="Student status updated successfully.",
        data=student_service.change_status(
            db,
            tenant.library_id,
            student_id,
            payload.status,
            tenant.user.id,
        ),
    )


@router.post(
    "/{student_id}/invitation",
    response_model=SuccessResponse[StudentInvitationResponse],
    operation_id="inviteStudent",
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(404, 409),
    openapi_extra={"x-user-stories": ["STUDENT-INVITE"]},
)
def invite_student(
    student_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[StudentInvitationResponse]:
    invitation = student_service.invite_student(
        db,
        tenant.library_id,
        student_id,
        tenant.user.id,
    )
    return SuccessResponse(
        message="Student portal invitation created successfully.",
        data=invitation,
    )


@router.delete(
    "/{student_id}",
    response_model=MessageResponse,
    operation_id="deleteStudent",
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["STUDENT-DELETE"]},
)
def delete_student(
    student_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> MessageResponse:
    student_service.delete_student(
        db,
        tenant.library_id,
        student_id,
        tenant.user.id,
    )
    return MessageResponse(message="Student deleted successfully.")
