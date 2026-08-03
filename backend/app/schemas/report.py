"""Owner dashboard and report API contracts."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import APIModel
from app.schemas.payment import MONTH_PATTERN


class ReportMonthOption(APIModel):
    value: str = Field(pattern=MONTH_PATTERN)
    label: str


class ReportFloorOption(APIModel):
    value: uuid.UUID
    label: str
    code: str


class ReportShiftOption(APIModel):
    value: uuid.UUID
    label: str
    timing: str
    start_time: str
    end_time: str
    is_active: bool


class ReportOptionsData(APIModel):
    months: list[ReportMonthOption]
    floors: list[ReportFloorOption]
    shifts: list[ReportShiftOption]


class ReportAppliedFilters(APIModel):
    start_month: str = Field(pattern=MONTH_PATTERN)
    end_month: str = Field(pattern=MONTH_PATTERN)
    floor_id: uuid.UUID | None
    shift_id: uuid.UUID | None
    report_date: date


class DashboardMetrics(APIModel):
    total_students: int = Field(ge=0)
    active_students: int = Field(ge=0)
    inactive_students: int = Field(ge=0)
    total_seats: int = Field(ge=0)
    occupied_seats: int = Field(ge=0)
    available_seats: int = Field(ge=0)
    maintenance_seats: int = Field(ge=0)
    blocked_seats: int = Field(ge=0)
    occupancy_rate: float = Field(ge=0, le=100)
    collected_amount: Decimal = Field(ge=0)
    expected_amount: Decimal = Field(ge=0)
    pending_amount: Decimal = Field(ge=0)
    overdue_amount: Decimal = Field(ge=0)
    paid_payment_count: int = Field(ge=0)
    unpaid_payment_count: int = Field(ge=0)
    partially_paid_count: int = Field(ge=0)
    pending_student_count: int = Field(ge=0)
    collection_rate: float = Field(ge=0, le=100)


class SeatStatusItem(APIModel):
    status: str
    label: str
    count: int = Field(ge=0)


class MonthlyCollectionItem(APIModel):
    month: str = Field(pattern=MONTH_PATTERN)
    collected_amount: Decimal = Field(ge=0)
    expected_amount: Decimal = Field(ge=0)
    pending_amount: Decimal = Field(ge=0)
    collection_rate: float = Field(ge=0, le=100)


class ShiftStatusItem(APIModel):
    key: str
    label: str
    count: int = Field(ge=0)


class DashboardShiftAvailability(APIModel):
    id: uuid.UUID
    name: str
    timing: str
    total_seats: int = Field(ge=0)
    occupancy_rate: float = Field(ge=0, le=100)
    statuses: list[ShiftStatusItem]


class AttentionStudentItem(APIModel):
    id: str
    student_id: uuid.UUID
    student_name: str
    enrollment_number: str
    attention_type: str
    severity: str
    message: str
    related_entity_id: uuid.UUID | None
    route_name: str = "adminStudentDetails"


class ActivityActor(APIModel):
    id: uuid.UUID
    name: str


class RecentActivityItem(APIModel):
    id: uuid.UUID
    type: str
    action: str
    entity_type: str
    entity_id: str | None
    title: str
    detail: str
    amount: Decimal | None
    actor: ActivityActor | None
    occurred_at: datetime


class OwnerDashboardData(APIModel):
    current_month: str = Field(pattern=MONTH_PATTERN)
    report_date: date
    metrics: DashboardMetrics
    seat_status: list[SeatStatusItem]
    monthly_collection: list[MonthlyCollectionItem]
    shift_availability: list[DashboardShiftAvailability]
    students_requiring_attention: list[AttentionStudentItem]
    recent_activity: list[RecentActivityItem]
    last_updated: datetime


class RevenueTotals(APIModel):
    expected: Decimal = Field(ge=0)
    collected: Decimal = Field(ge=0)
    pending: Decimal = Field(ge=0)
    collection_rate: float = Field(ge=0, le=100)
    payment_count: int = Field(ge=0)
    paid_count: int = Field(ge=0)
    partially_paid_count: int = Field(ge=0)
    unpaid_count: int = Field(ge=0)
    revenue_change: float


class RevenueSeriesItem(APIModel):
    month: str = Field(pattern=MONTH_PATTERN)
    label: str
    expected: Decimal = Field(ge=0)
    collected: Decimal = Field(ge=0)
    pending: Decimal = Field(ge=0)
    collection_rate: float = Field(ge=0, le=100)
    payment_count: int = Field(ge=0)


class PaymentMethodItem(APIModel):
    method: str
    label: str
    count: int = Field(ge=0)
    amount: Decimal = Field(ge=0)
    share: float = Field(ge=0, le=100)


class RevenueReport(APIModel):
    totals: RevenueTotals
    series: list[RevenueSeriesItem]
    payment_methods: list[PaymentMethodItem]


class OccupancyTotals(APIModel):
    total_seats: int = Field(ge=0)
    allocatable_seats: int = Field(ge=0)
    occupied_seats: int = Field(ge=0)
    available_seats: int = Field(ge=0)
    blocked_seats: int = Field(ge=0)
    maintenance_seats: int = Field(ge=0)
    occupancy_rate: float = Field(ge=0, le=100)


class ShiftOccupancyItem(APIModel):
    shift_id: uuid.UUID
    name: str
    timing: str
    total_seats: int = Field(ge=0)
    available: int = Field(ge=0)
    occupied: int = Field(ge=0)
    blocked: int = Field(ge=0)
    reserved: int = Field(ge=0)
    maintenance: int = Field(ge=0)
    occupancy_rate: float = Field(ge=0, le=100)


class FloorOccupancyItem(APIModel):
    floor: uuid.UUID
    label: str
    total_seats: int = Field(ge=0)
    occupied: int = Field(ge=0)
    available: int = Field(ge=0)
    blocked: int = Field(ge=0)
    maintenance: int = Field(ge=0)
    occupancy_rate: float = Field(ge=0, le=100)


class OccupancyReport(APIModel):
    totals: OccupancyTotals
    by_shift: list[ShiftOccupancyItem]
    by_floor: list[FloorOccupancyItem]


class StudentTotals(APIModel):
    total_students: int = Field(ge=0)
    active_students: int = Field(ge=0)
    inactive_students: int = Field(ge=0)
    left_students: int = Field(ge=0)
    suspended_students: int = Field(ge=0)
    active_rate: float = Field(ge=0, le=100)
    new_students: int = Field(ge=0)


class StudentTrendItem(APIModel):
    month: str = Field(pattern=MONTH_PATTERN)
    label: str
    joined: int = Field(ge=0)
    active_students_at_end: int = Field(ge=0)


class StudentDistributionItem(APIModel):
    status: str
    label: str
    count: int = Field(ge=0)


class StudentShiftItem(APIModel):
    shift_id: uuid.UUID
    count: int = Field(ge=0)


class StudentReport(APIModel):
    totals: StudentTotals
    joining_trend: list[StudentTrendItem]
    status_distribution: list[StudentDistributionItem]
    fee_status: list[StudentDistributionItem]
    shift_distribution: list[StudentShiftItem]


class PendingTotals(APIModel):
    pending_amount: Decimal = Field(ge=0)
    overdue_amount: Decimal = Field(ge=0)
    pending_count: int = Field(ge=0)
    overdue_count: int = Field(ge=0)
    affected_students: int = Field(ge=0)
    unpaid_count: int = Field(ge=0)
    partially_paid_count: int = Field(ge=0)


class AgeingItem(APIModel):
    key: str
    label: str
    count: int = Field(ge=0)
    student_count: int = Field(ge=0)
    outstanding_amount: Decimal = Field(ge=0)


class PendingPaymentItem(APIModel):
    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    enrollment_number: str
    phone: str
    seat_number: str
    month: str = Field(pattern=MONTH_PATTERN)
    month_label: str
    total_amount: Decimal = Field(ge=0)
    paid_amount: Decimal = Field(ge=0)
    amount: Decimal = Field(ge=0)
    due_date: date
    days_overdue: int = Field(ge=0)
    ageing_bucket: str
    ageing: str


class PendingPaymentsReport(APIModel):
    totals: PendingTotals
    records: list[PendingPaymentItem]
    ageing: list[AgeingItem]


class ReportInsight(APIModel):
    id: str
    tone: str
    title: str
    detail: str


class ReportOverviewMetrics(APIModel):
    collected_revenue: Decimal = Field(ge=0)
    pending_revenue: Decimal = Field(ge=0)
    collection_rate: float = Field(ge=0, le=100)
    active_students: int = Field(ge=0)
    total_students: int = Field(ge=0)
    occupied_seats: int = Field(ge=0)
    total_seats: int = Field(ge=0)
    occupancy_rate: float = Field(ge=0, le=100)


class OwnerReportsData(APIModel):
    generated_at: datetime
    filters: ReportAppliedFilters
    metrics: ReportOverviewMetrics
    revenue: RevenueReport
    occupancy: OccupancyReport
    students: StudentReport
    pending_payments: PendingPaymentsReport
    insights: list[ReportInsight]
