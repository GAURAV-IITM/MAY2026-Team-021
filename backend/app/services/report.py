"""Tenant-scoped Owner dashboard and report calculations."""
from __future__ import annotations

import calendar
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.models.audit import AuditLog
from app.models.enums import (
    PaymentTransactionStatus,
    SeatOperationalStatus,
    StudentStatus,
)
from app.models.payment import FeeRecord, PaymentTransaction
from app.models.seat import Floor, Seat, SeatAllocation, Shift
from app.models.student import Student
from app.repositories import report as repository
from app.schemas.report import (
    ActivityActor,
    AgeingItem,
    AttentionStudentItem,
    DashboardMetrics,
    DashboardShiftAvailability,
    FloorOccupancyItem,
    MonthlyCollectionItem,
    OccupancyReport,
    OccupancyTotals,
    OwnerDashboardData,
    OwnerReportsData,
    PaymentMethodItem,
    PendingPaymentItem,
    PendingPaymentsReport,
    PendingTotals,
    RecentActivityItem,
    ReportAppliedFilters,
    ReportFloorOption,
    ReportInsight,
    ReportMonthOption,
    ReportOptionsData,
    ReportOverviewMetrics,
    ReportShiftOption,
    RevenueReport,
    RevenueSeriesItem,
    RevenueTotals,
    SeatStatusItem,
    ShiftOccupancyItem,
    ShiftStatusItem,
    StudentDistributionItem,
    StudentReport,
    StudentShiftItem,
    StudentTotals,
    StudentTrendItem,
)
from app.services.allocation import time_ranges_overlap


ZERO = Decimal("0.00")
MONEY_UNIT = Decimal("0.01")
MAX_REPORT_MONTHS = 24
ATTENTION_LIMIT = 6
RECENT_ACTIVITY_LIMIT = 6
PENDING_DETAIL_LIMIT = 200


@dataclass(frozen=True, slots=True)
class FeeFinancial:
    fee: FeeRecord
    paid: Decimal
    balance: Decimal
    completed_transactions: tuple[PaymentTransaction, ...]


@dataclass(frozen=True, slots=True)
class SeatCounts:
    total: int
    allocatable: int
    available: int
    occupied: int
    blocked: int
    maintenance: int
    physically_blocked: int


def money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(MONEY_UNIT)


def percentage(part: Decimal | int, total: Decimal | int) -> float:
    denominator = Decimal(total)
    if denominator <= 0:
        return 0.0
    return float(
        ((Decimal(part) / denominator) * Decimal("100")).quantize(
            Decimal("0.01")
        )
    )


def _timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _local_today(timezone_name: str) -> date:
    return datetime.now(_timezone(timezone_name)).date()


def _month(value: str) -> date:
    try:
        year, month_number = (int(part) for part in value.split("-"))
        return date(year, month_number, 1)
    except (TypeError, ValueError):
        raise BusinessRuleError(
            "Report months must use YYYY-MM format.",
            code="REPORT_INVALID_MONTH_RANGE",
        ) from None


def _month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def _month_label(value: date) -> str:
    return value.strftime("%b %Y")


def _month_end(value: date) -> date:
    return date(
        value.year,
        value.month,
        calendar.monthrange(value.year, value.month)[1],
    )


def _add_months(value: date, offset: int) -> date:
    index = value.year * 12 + value.month - 1 + offset
    return date(index // 12, index % 12 + 1, 1)


def month_range(start: date, end: date) -> list[date]:
    months: list[date] = []
    current = start
    while current <= end:
        months.append(current)
        current = _add_months(current, 1)
    return months


def _normalize_month_range(
    timezone_name: str,
    *,
    start_month: str | None,
    end_month: str | None,
) -> tuple[date, date]:
    current_month = _local_today(timezone_name).replace(day=1)
    end = _month(end_month) if end_month else current_month
    start = (
        _month(start_month)
        if start_month
        else _add_months(end, -2)
    )
    if end < start:
        raise BusinessRuleError(
            "The report start month cannot be after the end month.",
            code="REPORT_INVALID_MONTH_RANGE",
        )
    if len(month_range(start, end)) > MAX_REPORT_MONTHS:
        raise BusinessRuleError(
            f"Reports may cover at most {MAX_REPORT_MONTHS} months.",
            code="REPORT_INVALID_MONTH_RANGE",
        )
    return start, end


def _require_floor(
    db: Session,
    library_id: uuid.UUID,
    floor_id: uuid.UUID | None,
) -> Floor | None:
    if floor_id is None:
        return None
    floor = repository.get_floor(db, library_id, floor_id)
    if floor is None:
        raise ResourceNotFoundError(
            "Report floor not found.",
            code="REPORT_FLOOR_NOT_FOUND",
        )
    return floor


def _require_shift(
    db: Session,
    library_id: uuid.UUID,
    shift_id: uuid.UUID | None,
) -> Shift | None:
    if shift_id is None:
        return None
    shift = repository.get_shift(db, library_id, shift_id)
    if shift is None:
        raise ResourceNotFoundError(
            "Report shift not found.",
            code="REPORT_SHIFT_NOT_FOUND",
        )
    return shift


def get_report_options(
    db: Session,
    library_id: uuid.UUID,
    timezone_name: str,
) -> ReportOptionsData:
    current_month = _local_today(timezone_name).replace(day=1)
    months = {
        _add_months(current_month, offset)
        for offset in range(-11, 1)
    }
    months.update(repository.list_all_fee_months(db, library_id))
    months.update(
        student.joined_on.replace(day=1)
        for student in repository.list_students(db, library_id)
    )
    local_timezone = _timezone(timezone_name)
    for paid_at in repository.list_payment_dates(db, library_id):
        if paid_at.tzinfo is None:
            paid_at = paid_at.replace(tzinfo=timezone.utc)
        local_date = paid_at.astimezone(local_timezone).date()
        months.add(local_date.replace(day=1))

    floors = repository.list_floors(db, library_id)
    shifts = repository.list_shifts(db, library_id)
    historical_shift_ids = repository.list_historical_shift_ids(
        db,
        library_id,
    )
    shifts = [
        shift
        for shift in shifts
        if shift.is_active or shift.id in historical_shift_ids
    ]
    return ReportOptionsData(
        months=[
            ReportMonthOption(
                value=_month_key(month),
                label=month.strftime("%B %Y"),
            )
            for month in sorted(months)
        ],
        floors=[
            ReportFloorOption(
                value=floor.id,
                label=floor.name,
                code=floor.code,
            )
            for floor in floors
        ],
        shifts=[
            ReportShiftOption(
                value=shift.id,
                label=shift.name,
                timing=(
                    f"{shift.start_time.strftime('%H:%M')} - "
                    f"{shift.end_time.strftime('%H:%M')}"
                ),
                start_time=shift.start_time.strftime("%H:%M"),
                end_time=shift.end_time.strftime("%H:%M"),
                is_active=shift.is_active,
            )
            for shift in shifts
        ],
    )


def _completed_transactions(
    fee: FeeRecord,
) -> tuple[PaymentTransaction, ...]:
    return tuple(
        transaction
        for transaction in fee.transactions
        if transaction.status == PaymentTransactionStatus.COMPLETED
    )


def _fee_financials(fees: list[FeeRecord]) -> list[FeeFinancial]:
    result = []
    for fee in fees:
        transactions = _completed_transactions(fee)
        paid = money(sum((item.amount for item in transactions), ZERO))
        balance = max(money(fee.total_amount) - paid, ZERO)
        result.append(
            FeeFinancial(
                fee=fee,
                paid=paid,
                balance=balance,
                completed_transactions=transactions,
            )
        )
    return result


def _fee_state(financial: FeeFinancial) -> str:
    if financial.balance == ZERO:
        return "paid"
    if financial.paid > ZERO:
        return "partially_paid"
    return "unpaid"


def _revenue_report(
    financials: list[FeeFinancial],
    months: list[date],
) -> RevenueReport:
    series = []
    all_transactions: list[PaymentTransaction] = []
    paid_count = partially_paid_count = unpaid_count = 0
    for month in months:
        records = [
            item
            for item in financials
            if item.fee.billing_month == month
        ]
        expected = money(
            sum((item.fee.total_amount for item in records), ZERO)
        )
        collected = money(sum((item.paid for item in records), ZERO))
        pending = money(sum((item.balance for item in records), ZERO))
        transactions = [
            transaction
            for item in records
            for transaction in item.completed_transactions
        ]
        all_transactions.extend(transactions)
        for item in records:
            state = _fee_state(item)
            if state == "paid":
                paid_count += 1
            elif state == "partially_paid":
                partially_paid_count += 1
            else:
                unpaid_count += 1
        series.append(
            RevenueSeriesItem(
                month=_month_key(month),
                label=_month_label(month),
                expected=expected,
                collected=collected,
                pending=pending,
                collection_rate=percentage(collected, expected),
                payment_count=len(transactions),
            )
        )

    expected = money(sum((item.expected for item in series), ZERO))
    collected = money(sum((item.collected for item in series), ZERO))
    pending = money(sum((item.pending for item in series), ZERO))
    latest = series[-1].collected if series else ZERO
    previous = series[-2].collected if len(series) > 1 else ZERO
    revenue_change = (
        percentage(latest - previous, previous)
        if previous
        else (100.0 if latest else 0.0)
    )

    by_method: dict[str, list[PaymentTransaction]] = defaultdict(list)
    for transaction in all_transactions:
        by_method[transaction.method.value].append(transaction)
    method_items = []
    for method, transactions in sorted(by_method.items()):
        method_items.append(
            PaymentMethodItem(
                method=method,
                label=method.replace("_", " ").title(),
                count=len(transactions),
                amount=money(
                    sum((item.amount for item in transactions), ZERO)
                ),
                share=percentage(len(transactions), len(all_transactions)),
            )
        )

    return RevenueReport(
        totals=RevenueTotals(
            expected=expected,
            collected=collected,
            pending=pending,
            collection_rate=percentage(collected, expected),
            payment_count=len(all_transactions),
            paid_count=paid_count,
            partially_paid_count=partially_paid_count,
            unpaid_count=unpaid_count,
            revenue_change=revenue_change,
        ),
        series=series,
        payment_methods=method_items,
    )


def ageing_bucket(days_overdue: int) -> tuple[str, str]:
    if days_overdue <= 0:
        return "not_due", "Not due"
    if days_overdue <= 30:
        return "1_30", "1-30 days"
    if days_overdue <= 60:
        return "31_60", "31-60 days"
    if days_overdue <= 90:
        return "61_90", "61-90 days"
    return "90_plus", "More than 90 days"


AGEING_BUCKETS = (
    ("not_due", "Not due"),
    ("1_30", "1-30 days"),
    ("31_60", "31-60 days"),
    ("61_90", "61-90 days"),
    ("90_plus", "More than 90 days"),
)


def _pending_report(
    financials: list[FeeFinancial],
    report_date: date,
    allocations: list[SeatAllocation],
) -> PendingPaymentsReport:
    allocation_by_student: dict[uuid.UUID, SeatAllocation] = {}
    for allocation in allocations:
        allocation_by_student.setdefault(allocation.student_id, allocation)

    records: list[PendingPaymentItem] = []
    bucket_records: dict[str, list[PendingPaymentItem]] = defaultdict(list)
    unpaid_count = partially_paid_count = 0
    for item in financials:
        if item.balance <= ZERO:
            continue
        state = _fee_state(item)
        if state == "partially_paid":
            partially_paid_count += 1
        else:
            unpaid_count += 1
        days_overdue = max((report_date - item.fee.due_date).days, 0)
        bucket, bucket_label = ageing_bucket(
            (report_date - item.fee.due_date).days
        )
        allocation = allocation_by_student.get(item.fee.student_id)
        record = PendingPaymentItem(
            id=item.fee.id,
            student_id=item.fee.student_id,
            student_name=(
                f"{item.fee.student.first_name} "
                f"{item.fee.student.last_name}"
            ).strip(),
            enrollment_number=item.fee.student.enrollment_number,
            phone=item.fee.student.phone,
            seat_number=(
                allocation.seat_number_snapshot
                or allocation.seat.seat_number
                if allocation
                else "Not assigned"
            ),
            month=_month_key(item.fee.billing_month),
            month_label=_month_label(item.fee.billing_month),
            total_amount=money(item.fee.total_amount),
            paid_amount=item.paid,
            amount=item.balance,
            due_date=item.fee.due_date,
            days_overdue=days_overdue,
            ageing_bucket=bucket,
            ageing=(
                f"{days_overdue} days overdue"
                if days_overdue
                else bucket_label
            ),
        )
        records.append(record)
        bucket_records[bucket].append(record)

    records.sort(
        key=lambda item: (
            -item.days_overdue,
            -item.amount,
            item.student_name,
            str(item.id),
        )
    )
    ageing = [
        AgeingItem(
            key=key,
            label=label,
            count=len(bucket_records[key]),
            student_count=len(
                {item.student_id for item in bucket_records[key]}
            ),
            outstanding_amount=money(
                sum(
                    (item.amount for item in bucket_records[key]),
                    ZERO,
                )
            ),
        )
        for key, label in AGEING_BUCKETS
    ]
    overdue_records = [item for item in records if item.days_overdue > 0]
    return PendingPaymentsReport(
        totals=PendingTotals(
            pending_amount=money(
                sum((item.amount for item in records), ZERO)
            ),
            overdue_amount=money(
                sum((item.amount for item in overdue_records), ZERO)
            ),
            pending_count=len(records),
            overdue_count=len(overdue_records),
            affected_students=len(
                {item.student_id for item in records}
            ),
            unpaid_count=unpaid_count,
            partially_paid_count=partially_paid_count,
        ),
        records=records[:PENDING_DETAIL_LIMIT],
        ageing=ageing,
    )


def _allocations_by_seat(
    allocations: list[SeatAllocation],
) -> dict[uuid.UUID, list[SeatAllocation]]:
    result: dict[uuid.UUID, list[SeatAllocation]] = defaultdict(list)
    for allocation in allocations:
        result[allocation.seat_id].append(allocation)
    return result


def _allocation_overlaps_shift(
    allocation: SeatAllocation,
    shift: Shift,
) -> bool:
    return time_ranges_overlap(
        allocation.shift_start_time,
        allocation.shift_end_time,
        shift.start_time,
        shift.end_time,
    )


def _seat_state(
    seat: Seat,
    allocations: list[SeatAllocation],
    selected_shift: Shift | None,
) -> str:
    if seat.operational_status == SeatOperationalStatus.MAINTENANCE:
        return "maintenance"
    if seat.operational_status == SeatOperationalStatus.BLOCKED:
        return "physically_blocked"
    if selected_shift is None:
        return "occupied" if allocations else "available"
    if any(
        allocation.shift_id == selected_shift.id
        for allocation in allocations
    ):
        return "occupied"
    if any(
        _allocation_overlaps_shift(allocation, selected_shift)
        for allocation in allocations
    ):
        return "allocation_blocked"
    return "available"


def _seat_counts(
    seats: list[Seat],
    allocations: list[SeatAllocation],
    selected_shift: Shift | None,
) -> SeatCounts:
    by_seat = _allocations_by_seat(allocations)
    states = [
        _seat_state(seat, by_seat.get(seat.id, []), selected_shift)
        for seat in seats
    ]
    maintenance = states.count("maintenance")
    physically_blocked = states.count("physically_blocked")
    allocation_blocked = states.count("allocation_blocked")
    return SeatCounts(
        total=len(seats),
        allocatable=max(
            len(seats) - maintenance - physically_blocked,
            0,
        ),
        available=states.count("available"),
        occupied=states.count("occupied"),
        blocked=physically_blocked + allocation_blocked,
        maintenance=maintenance,
        physically_blocked=physically_blocked,
    )


def _shift_item(
    shift: Shift,
    seats: list[Seat],
    allocations: list[SeatAllocation],
) -> ShiftOccupancyItem:
    counts = _seat_counts(seats, allocations, shift)
    return ShiftOccupancyItem(
        shift_id=shift.id,
        name=shift.name,
        timing=(
            f"{shift.start_time.strftime('%H:%M')} - "
            f"{shift.end_time.strftime('%H:%M')}"
        ),
        total_seats=counts.total,
        available=counts.available,
        occupied=counts.occupied,
        blocked=counts.blocked,
        reserved=0,
        maintenance=counts.maintenance,
        occupancy_rate=percentage(counts.occupied, counts.allocatable),
    )


def _occupancy_report(
    seats: list[Seat],
    floors: list[Floor],
    shifts: list[Shift],
    allocations: list[SeatAllocation],
    selected_shift: Shift | None,
) -> OccupancyReport:
    counts = _seat_counts(seats, allocations, selected_shift)
    shown_shifts = (
        [selected_shift]
        if selected_shift
        else [shift for shift in shifts if shift.is_active]
    )
    by_floor = []
    for floor in floors:
        floor_seats = [seat for seat in seats if seat.floor_id == floor.id]
        if not floor_seats:
            continue
        seat_ids = {seat.id for seat in floor_seats}
        floor_allocations = [
            allocation
            for allocation in allocations
            if allocation.seat_id in seat_ids
        ]
        floor_counts = _seat_counts(
            floor_seats,
            floor_allocations,
            selected_shift,
        )
        by_floor.append(
            FloorOccupancyItem(
                floor=floor.id,
                label=floor.name,
                total_seats=floor_counts.total,
                occupied=floor_counts.occupied,
                available=floor_counts.available,
                blocked=floor_counts.blocked,
                maintenance=floor_counts.maintenance,
                occupancy_rate=percentage(
                    floor_counts.occupied,
                    floor_counts.allocatable,
                ),
            )
        )
    return OccupancyReport(
        totals=OccupancyTotals(
            total_seats=counts.total,
            allocatable_seats=counts.allocatable,
            occupied_seats=counts.occupied,
            available_seats=counts.available,
            blocked_seats=counts.blocked,
            maintenance_seats=counts.maintenance,
            occupancy_rate=percentage(
                counts.occupied,
                counts.allocatable,
            ),
        ),
        by_shift=[
            _shift_item(shift, seats, allocations)
            for shift in shown_shifts
        ],
        by_floor=by_floor,
    )


def _scoped_students(
    students: list[Student],
    allocations: list[SeatAllocation],
    *,
    floor_id: uuid.UUID | None,
    shift_id: uuid.UUID | None,
) -> list[Student]:
    if floor_id is None and shift_id is None:
        return students
    student_ids = set()
    for allocation in allocations:
        if (
            floor_id is not None
            and allocation.seat.floor_id != floor_id
        ):
            continue
        if shift_id is not None and allocation.shift_id != shift_id:
            continue
        student_ids.add(allocation.student_id)
    return [student for student in students if student.id in student_ids]


def _student_report(
    students: list[Student],
    months: list[date],
    allocations: list[SeatAllocation],
    financials: list[FeeFinancial],
    report_date: date,
) -> StudentReport:
    status_counts = {
        status: sum(student.status == status for student in students)
        for status in StudentStatus
    }
    financials_by_student: dict[uuid.UUID, list[FeeFinancial]] = defaultdict(
        list
    )
    for financial in financials:
        financials_by_student[financial.fee.student_id].append(financial)

    fee_status_counts = {
        "paid": 0,
        "pending": 0,
        "overdue": 0,
        "not_recorded": 0,
    }
    for student in students:
        student_financials = financials_by_student.get(student.id, [])
        if not student_financials:
            fee_status_counts["not_recorded"] += 1
        elif any(
            item.balance > ZERO and item.fee.due_date < report_date
            for item in student_financials
        ):
            fee_status_counts["overdue"] += 1
        elif any(item.balance > ZERO for item in student_financials):
            fee_status_counts["pending"] += 1
        else:
            fee_status_counts["paid"] += 1

    student_ids = {student.id for student in students}
    by_shift: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
    for allocation in allocations:
        if allocation.student_id in student_ids:
            by_shift[allocation.shift_id].add(allocation.student_id)

    trend = []
    for month in months:
        end = _month_end(month)
        trend.append(
            StudentTrendItem(
                month=_month_key(month),
                label=_month_label(month),
                joined=sum(
                    student.joined_on.replace(day=1) == month
                    for student in students
                ),
                active_students_at_end=sum(
                    student.status == StudentStatus.ACTIVE
                    and student.joined_on <= end
                    for student in students
                ),
            )
        )
    total = len(students)
    active = status_counts[StudentStatus.ACTIVE]
    labels = {
        StudentStatus.ACTIVE: "Active",
        StudentStatus.INACTIVE: "Inactive",
        StudentStatus.LEFT: "Left",
        StudentStatus.SUSPENDED: "Suspended",
    }
    fee_labels = {
        "paid": "Paid",
        "pending": "Pending",
        "overdue": "Overdue",
        "not_recorded": "No fee record",
    }
    return StudentReport(
        totals=StudentTotals(
            total_students=total,
            active_students=active,
            inactive_students=status_counts[StudentStatus.INACTIVE],
            left_students=status_counts[StudentStatus.LEFT],
            suspended_students=status_counts[StudentStatus.SUSPENDED],
            active_rate=percentage(active, total),
            new_students=sum(
                student.joined_on.replace(day=1) in set(months)
                for student in students
            ),
        ),
        joining_trend=trend,
        status_distribution=[
            StudentDistributionItem(
                status=status.value,
                label=labels[status],
                count=status_counts[status],
            )
            for status in StudentStatus
        ],
        fee_status=[
            StudentDistributionItem(
                status=status,
                label=fee_labels[status],
                count=count,
            )
            for status, count in fee_status_counts.items()
        ],
        shift_distribution=[
            StudentShiftItem(shift_id=shift_id, count=len(student_ids))
            for shift_id, student_ids in sorted(
                by_shift.items(),
                key=lambda item: str(item[0]),
            )
        ],
    )


def _insights(
    revenue: RevenueReport,
    occupancy: OccupancyReport,
    students: StudentReport,
    pending: PendingPaymentsReport,
) -> list[ReportInsight]:
    collection_healthy = revenue.totals.collection_rate >= 85
    occupancy_high = occupancy.totals.occupancy_rate >= 90
    return [
        ReportInsight(
            id="collection-health",
            tone="success" if collection_healthy else "warning",
            title=(
                "Collections are on track"
                if collection_healthy
                else "Collections need attention"
            ),
            detail=(
                f"{revenue.totals.collection_rate:g}% of billed fees were "
                "collected in this period."
            ),
        ),
        ReportInsight(
            id="seat-capacity",
            tone="warning" if occupancy_high else "info",
            title=(
                "Seat capacity is running high"
                if occupancy_high
                else "Seat capacity is available"
            ),
            detail=(
                f"{occupancy.totals.occupancy_rate:g}% occupancy on the "
                f"{occupancy.totals.total_seats} scoped seats."
            ),
        ),
        ReportInsight(
            id="student-health",
            tone="neutral",
            title=f"{students.totals.active_students} active students",
            detail=(
                f"{pending.totals.affected_students} students have a "
                "calculated outstanding balance."
            ),
        ),
    ]


def get_reports(
    db: Session,
    library_id: uuid.UUID,
    timezone_name: str,
    *,
    start_month: str | None = None,
    end_month: str | None = None,
    floor_id: uuid.UUID | None = None,
    shift_id: uuid.UUID | None = None,
) -> OwnerReportsData:
    start, end = _normalize_month_range(
        timezone_name,
        start_month=start_month,
        end_month=end_month,
    )
    _require_floor(db, library_id, floor_id)
    selected_shift = _require_shift(db, library_id, shift_id)
    local_today = _local_today(timezone_name)
    report_date = min(local_today, _month_end(end))
    months = month_range(start, end)

    students = repository.list_students(db, library_id)
    floors = repository.list_floors(db, library_id)
    if floor_id is not None:
        floors = [floor for floor in floors if floor.id == floor_id]
    shifts = repository.list_shifts(db, library_id)
    seats = repository.list_seats(
        db,
        library_id,
        floor_id=floor_id,
    )
    allocations = repository.list_allocations_on_date(
        db,
        library_id,
        report_date,
        seat_ids={seat.id for seat in seats},
    )
    scoped_students = _scoped_students(
        students,
        allocations,
        floor_id=floor_id,
        shift_id=shift_id,
    )
    fees = repository.list_fee_records(
        db,
        library_id,
        start,
        end,
        student_ids=(
            {student.id for student in scoped_students}
            if floor_id is not None or shift_id is not None
            else None
        ),
    )
    financials = _fee_financials(fees)
    revenue = _revenue_report(financials, months)
    occupancy = _occupancy_report(
        seats,
        floors,
        shifts,
        allocations,
        selected_shift,
    )
    student_report = _student_report(
        scoped_students,
        months,
        allocations,
        financials,
        report_date,
    )
    pending = _pending_report(financials, report_date, allocations)
    return OwnerReportsData(
        generated_at=datetime.now(timezone.utc),
        filters=ReportAppliedFilters(
            start_month=_month_key(start),
            end_month=_month_key(end),
            floor_id=floor_id,
            shift_id=shift_id,
            report_date=report_date,
        ),
        metrics=ReportOverviewMetrics(
            collected_revenue=revenue.totals.collected,
            pending_revenue=revenue.totals.pending,
            collection_rate=revenue.totals.collection_rate,
            active_students=student_report.totals.active_students,
            total_students=student_report.totals.total_students,
            occupied_seats=occupancy.totals.occupied_seats,
            total_seats=occupancy.totals.total_seats,
            occupancy_rate=occupancy.totals.occupancy_rate,
        ),
        revenue=revenue,
        occupancy=occupancy,
        students=student_report,
        pending_payments=pending,
        insights=_insights(
            revenue,
            occupancy,
            student_report,
            pending,
        ),
    )


ACTIVITY_TITLES = {
    "payment_transaction.recorded": ("payment", "Payment recorded"),
    "receipt.issued": ("payment", "Receipt issued"),
    "monthly_fees.generated": ("payment", "Monthly fees generated"),
    "payment_reminder.link_generated": ("payment", "Reminder prepared"),
    "seat_allocation.created": ("allocation", "Seat allocation created"),
    "seat_allocation.completed": ("allocation", "Seat allocation completed"),
    "seat_allocation.cancelled": ("allocation", "Seat allocation cancelled"),
    "seat_change_request.approved": (
        "request",
        "Seat request approved",
    ),
    "seat_change_request.rejected": (
        "request",
        "Seat request rejected",
    ),
    "announcement.created": ("announcement", "Announcement created"),
    "announcement.published": ("announcement", "Announcement published"),
    "announcement.archived": ("announcement", "Announcement archived"),
}


def _activity(audit: AuditLog) -> RecentActivityItem:
    activity_type, title = ACTIVITY_TITLES.get(
        audit.action,
        ("activity", audit.action.replace(".", " ").replace("_", " ").title()),
    )
    values = audit.new_values or {}
    raw_amount = values.get("amount")
    try:
        amount = money(raw_amount) if raw_amount is not None else None
    except (ValueError, TypeError):
        amount = None
    actor = audit.actor
    return RecentActivityItem(
        id=audit.id,
        type=activity_type,
        action=audit.action,
        entity_type=audit.entity_type,
        entity_id=audit.entity_id,
        title=title,
        detail=(
            f"By {actor.full_name}"
            if actor
            else "Recorded by the system"
        ),
        amount=amount,
        actor=(
            ActivityActor(id=actor.id, name=actor.full_name)
            if actor
            else None
        ),
        occurred_at=audit.created_at,
    )


def _attention_items(
    students: list[Student],
    allocations: list[SeatAllocation],
    financials: list[FeeFinancial],
    pending_requests,
    report_date: date,
) -> list[AttentionStudentItem]:
    allocations_by_student: dict[uuid.UUID, list[SeatAllocation]] = (
        defaultdict(list)
    )
    for allocation in allocations:
        allocations_by_student[allocation.student_id].append(allocation)
    overdue_by_student: dict[uuid.UUID, FeeFinancial] = {}
    for financial in financials:
        if (
            financial.balance > ZERO
            and financial.fee.due_date < report_date
        ):
            current = overdue_by_student.get(financial.fee.student_id)
            if current is None or financial.balance > current.balance:
                overdue_by_student[financial.fee.student_id] = financial
    request_by_student = {
        request.student_id: request for request in pending_requests
    }
    candidates: list[tuple[int, Decimal, AttentionStudentItem]] = []
    for student in students:
        name = f"{student.first_name} {student.last_name}".strip()
        student_allocations = allocations_by_student.get(student.id, [])
        priority = 99
        balance = ZERO
        item = None
        if (
            student.status != StudentStatus.ACTIVE
            and student_allocations
        ):
            priority = 0
            item = AttentionStudentItem(
                id=f"inconsistent-allocation-{student.id}",
                student_id=student.id,
                student_name=name,
                enrollment_number=student.enrollment_number,
                attention_type="inactiveWithAllocation",
                severity="critical",
                message="A non-active student still has an active allocation.",
                related_entity_id=student_allocations[0].id,
            )
        elif student.id in overdue_by_student:
            priority = 1
            overdue = overdue_by_student[student.id]
            balance = overdue.balance
            item = AttentionStudentItem(
                id=f"overdue-payment-{student.id}",
                student_id=student.id,
                student_name=name,
                enrollment_number=student.enrollment_number,
                attention_type="overduePayment",
                severity="high",
                message=(
                    f"Outstanding balance of {overdue.balance} is overdue."
                ),
                related_entity_id=overdue.fee.id,
            )
        elif student.id in request_by_student:
            priority = 2
            request = request_by_student[student.id]
            item = AttentionStudentItem(
                id=f"pending-request-{student.id}",
                student_id=student.id,
                student_name=name,
                enrollment_number=student.enrollment_number,
                attention_type="pendingSeatRequest",
                severity="medium",
                message="A seat-change request is awaiting review.",
                related_entity_id=request.id,
            )
        elif (
            student.status == StudentStatus.ACTIVE
            and not student_allocations
        ):
            priority = 3
            item = AttentionStudentItem(
                id=f"missing-allocation-{student.id}",
                student_id=student.id,
                student_name=name,
                enrollment_number=student.enrollment_number,
                attention_type="missingAllocation",
                severity="medium",
                message="Active student has no seat allocation for this date.",
                related_entity_id=None,
            )
        elif student_allocations:
            expiring = min(
                student_allocations,
                key=lambda allocation: allocation.end_date,
            )
            days_remaining = (expiring.end_date - report_date).days
            if 0 <= days_remaining <= 7:
                priority = 4
                item = AttentionStudentItem(
                    id=f"expiring-allocation-{student.id}",
                    student_id=student.id,
                    student_name=name,
                    enrollment_number=student.enrollment_number,
                    attention_type="expiringAllocation",
                    severity="low",
                    message=(
                        f"Seat allocation ends in {days_remaining} days."
                    ),
                    related_entity_id=expiring.id,
                )
        if item is not None:
            candidates.append((priority, -balance, item))
    candidates.sort(
        key=lambda row: (
            row[0],
            row[1],
            row[2].student_name,
            str(row[2].student_id),
        )
    )
    return [row[2] for row in candidates[:ATTENTION_LIMIT]]


def get_dashboard(
    db: Session,
    library_id: uuid.UUID,
    timezone_name: str,
    *,
    report_date: date | None = None,
    billing_month: str | None = None,
) -> OwnerDashboardData:
    selected_date = report_date or _local_today(timezone_name)
    month = (
        _month(billing_month)
        if billing_month
        else selected_date.replace(day=1)
    )
    students = repository.list_students(db, library_id)
    floors = repository.list_floors(db, library_id)
    shifts = repository.list_shifts(db, library_id)
    seats = repository.list_seats(db, library_id)
    allocations = repository.list_allocations_on_date(
        db,
        library_id,
        selected_date,
        seat_ids={seat.id for seat in seats},
    )
    finance_start = _add_months(month, -11)
    fees = repository.list_fee_records(
        db,
        library_id,
        finance_start,
        month,
    )
    all_financials = _fee_financials(fees)
    current_financials = [
        item
        for item in all_financials
        if item.fee.billing_month == month
    ]
    current_revenue = _revenue_report(current_financials, [month])
    pending = _pending_report(
        current_financials,
        selected_date,
        allocations,
    )
    collection_months = month_range(_add_months(month, -2), month)
    collection_financials = [
        item
        for item in all_financials
        if item.fee.billing_month in set(collection_months)
    ]
    collection = _revenue_report(
        collection_financials,
        collection_months,
    )
    counts = _seat_counts(seats, allocations, None)
    active_students = sum(
        student.status == StudentStatus.ACTIVE for student in students
    )
    pending_requests = repository.list_pending_requests(db, library_id)
    activities = repository.list_recent_audits(
        db,
        library_id,
        limit=RECENT_ACTIVITY_LIMIT,
    )
    shifts = [shift for shift in shifts if shift.is_active]
    shift_items = [
        _shift_item(shift, seats, allocations) for shift in shifts
    ]
    return OwnerDashboardData(
        current_month=_month_key(month),
        report_date=selected_date,
        metrics=DashboardMetrics(
            total_students=len(students),
            active_students=active_students,
            inactive_students=len(students) - active_students,
            total_seats=counts.total,
            occupied_seats=counts.occupied,
            available_seats=counts.available,
            maintenance_seats=counts.maintenance,
            blocked_seats=counts.blocked,
            occupancy_rate=percentage(
                counts.occupied,
                counts.allocatable,
            ),
            collected_amount=current_revenue.totals.collected,
            expected_amount=current_revenue.totals.expected,
            pending_amount=pending.totals.pending_amount,
            overdue_amount=pending.totals.overdue_amount,
            paid_payment_count=current_revenue.totals.paid_count,
            unpaid_payment_count=current_revenue.totals.unpaid_count,
            partially_paid_count=(
                current_revenue.totals.partially_paid_count
            ),
            pending_student_count=pending.totals.affected_students,
            collection_rate=current_revenue.totals.collection_rate,
        ),
        seat_status=[
            SeatStatusItem(
                status="available",
                label="Available",
                count=counts.available,
            ),
            SeatStatusItem(
                status="occupied",
                label="Occupied",
                count=counts.occupied,
            ),
            SeatStatusItem(
                status="reserved",
                label="Reserved",
                count=0,
            ),
            SeatStatusItem(
                status="maintenance",
                label="Maintenance",
                count=counts.maintenance,
            ),
            SeatStatusItem(
                status="blocked",
                label="Blocked",
                count=counts.blocked,
            ),
        ],
        monthly_collection=[
            MonthlyCollectionItem(
                month=item.month,
                collected_amount=item.collected,
                expected_amount=item.expected,
                pending_amount=item.pending,
                collection_rate=item.collection_rate,
            )
            for item in collection.series
        ],
        shift_availability=[
            DashboardShiftAvailability(
                id=item.shift_id,
                name=item.name,
                timing=item.timing,
                total_seats=item.total_seats,
                occupancy_rate=item.occupancy_rate,
                statuses=[
                    ShiftStatusItem(
                        key="available",
                        label="Available",
                        count=item.available,
                    ),
                    ShiftStatusItem(
                        key="occupied",
                        label="Allotted",
                        count=item.occupied,
                    ),
                    ShiftStatusItem(
                        key="blocked",
                        label="Blocked",
                        count=item.blocked,
                    ),
                    ShiftStatusItem(
                        key="reserved",
                        label="Reserved",
                        count=item.reserved,
                    ),
                    ShiftStatusItem(
                        key="maintenance",
                        label="Maintenance",
                        count=item.maintenance,
                    ),
                ],
            )
            for item in shift_items
        ],
        students_requiring_attention=_attention_items(
            students,
            allocations,
            all_financials,
            pending_requests,
            selected_date,
        ),
        recent_activity=[_activity(audit) for audit in activities],
        last_updated=datetime.now(timezone.utc),
    )
