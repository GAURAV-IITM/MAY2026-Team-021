from enum import StrEnum
from typing import TypeVar

from sqlalchemy import Enum as SQLAlchemyEnum


EnumType = TypeVar("EnumType", bound=StrEnum)


def enum_type(enum_class: type[EnumType], name: str) -> SQLAlchemyEnum:
    return SQLAlchemyEnum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )


class RoleName(StrEnum):
    SUPER_ADMIN = "super_admin"
    LIBRARY_OWNER = "library_owner"
    STAFF = "staff"
    STUDENT = "student"


class LibraryStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class MembershipStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LEFT = "left"


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class StudentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEFT = "left"
    SUSPENDED = "suspended"


class SeatOperationalStatus(StrEnum):
    AVAILABLE = "available"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"


class SeatType(StrEnum):
    STANDARD = "standard"
    PREMIUM = "premium"
    CABIN = "cabin"
    ACCESSIBLE = "accessible"


class AllocationStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SeatRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class FeeStatus(StrEnum):
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    WAIVED = "waived"
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    CASH = "cash"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    OTHER = "other"


class PaymentTransactionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ReminderChannel(StrEnum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"


class DeliveryStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class AnnouncementStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class AnnouncementPriority(StrEnum):
    NORMAL = "normal"
    IMPORTANT = "important"


class AnnouncementCategory(StrEnum):
    GENERAL = "general"
    SCHEDULE = "schedule"
    FEES = "fees"
    POLICY = "policy"
    FACILITY = "facility"


class AnnouncementAudience(StrEnum):
    ALL_STUDENTS = "all_students"
    ACTIVE_STUDENTS = "active_students"
    PENDING_FEE_STUDENTS = "pending_fee_students"
