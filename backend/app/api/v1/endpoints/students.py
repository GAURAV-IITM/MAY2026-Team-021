"""Tenant-scoped student management endpoints."""
from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
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
)
from app.services import student as student_service


router = APIRouter(
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(401, 403, 500),
)


@router.get(
    "",
    response_model=PaginatedResponse[StudentResponse],
    operation_id="listStudents",
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
        ),
    )


@router.patch(
    "/{student_id}/status",
    response_model=SuccessResponse[StudentResponse],
    operation_id="changeStudentStatus",
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
        ),
    )


@router.post(
    "/{student_id}/invitation",
    response_model=SuccessResponse[StudentInvitationResponse],
    operation_id="inviteStudent",
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
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["STUDENT-DELETE"]},
)
def delete_student(
    student_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> MessageResponse:
    student_service.delete_student(db, tenant.library_id, student_id)
    return MessageResponse(message="Student deleted successfully.")
