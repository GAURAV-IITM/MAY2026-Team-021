from sqlalchemy.orm import relationship
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String,Boolean 
from datetime import datetime
from database import Base 


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True,nullable=False)
    password_hash = Column(String(255),nullable=False)
    full_name = Column(String(100),nullable=False)
    phone=Column(String(20),unique=True)
    is_active = Column(Boolean,default=True)
    created_at = Column(DateTime,default=datetime.utcnow)

    #relationships 
    user_roles = relationship('UserRoles',back_populates='user')
    sessions = relationship('User_sessions',back_populates='user')
    library_membership= relationship('Library_Memberships',back_populates='user')
    students = relationship('Student',back_populates='user')


class Roles(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100),nullable=False)
    description = Column(String(100),nullable=False)

    user_roles = relationship('UserRoles',back_populates='role')

class UserRoles(Base):
    __tablename__ = "userroles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    role_id = Column(Integer,ForeignKey('roles.id'),nullable=False)

    user = relationship('Users',back_populates='user_roles')
    role = relationship('Roles',back_populates='user_roles')

class User_Sessions(Base):
    __tablename__ = 'user_session'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    refresh_token = Column(String)
    user_session_expires_at = Column(DateTime)
    device_info = Column(String)
    ip_address = Column(String)

   
    user = relationship('Users',back_populates='sessions')


class Announcements(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    library_id =Column(Integer,ForeignKey('libraries.id'))
    title = Column(String(100),nullable= True)
    description = Column(String(255),nullable=False)
    created_by = Column(Integer,ForeignKey('users.id'))
    announcement_created_at = Column(DateTime, default = datetime.utcnow)
    announcement_expires_at = Column(DateTime)

    user = relationship('Users',foreign_keys=[created_by])
    library = relationship('Libraries',back_populates='announcements')

class Library_Memberships(Base):
    __tablename__ = "library_memberships"

    id = Column(Integer, primary_key=True, index=True)
    library_id =Column(Integer,ForeignKey('libraries.id'))
    user_id = Column(Integer,ForeignKey('users.id'))
    role = Column(String)

    library = relationship('Libraries',back_populates='memberships')
    user = relationship('Users',back_populates='library_memberships')

class Fee_Receipts(Base):
    __tablename__ = 'fee_receipt'

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer,ForeignKey('payments.id'))
    receipt_number=Column(String,nullable=False)
    issued_at = Column(DateTime,default= datetime.utcnow)
    issued_by = Column(Integer,ForeignKey('users.id'),nullable=False)

    payment = relationship('Payment',back_populates='receipt')
    issuer = relationship('Users',foreign_keys=[issued_by])


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    library_id = Column(Integer, ForeignKey("libraries.id"), nullable=False)
    enrollment_no = Column(String(30), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    photo_url = Column(String(255))
    phone = Column(String(15), unique=True)
    email = Column(String(255), unique=True, nullable=False)
    address = Column(String(255))
    guardian_name = Column(String(100))
    guardian_phone = Column(String(15))
    date_of_birth = Column(Date)
    course = Column(String(100))
    department = Column(String(100))
    year = Column(String(20))
    admission_date = Column(Date)
    notes = Column(String)
    is_active = Column(Boolean, default=True)

    user = relationship("Users", back_populates="students")
    library = relationship("Libraries", back_populates="students")
    student_shifts = relationship("Student_Shifts", back_populates="student")
    payments = relationship("Payment", back_populates="student")
    seat_change_requests = relationship("SeatChangeRequest", back_populates="student")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    library_id = Column(Integer, ForeignKey("libraries.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0)
    late_fee = Column(Numeric(10, 2))
    payment_type = Column(String(50), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_gateway = Column(String(100))
    transaction_id = Column(String(100), unique=True)
    reference_number = Column(String(100), unique=True)
    due_date = Column(Date)
    paid_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(30), nullable=False)
    remarks = Column(String(255))

    student = relationship("Student", back_populates="payments")
    library = relationship("Libraries", back_populates="payments")
    receipt = relationship("Fee_Receipts", back_populates="payment", uselist=False)

class SeatChangeRequest(Base):
    __tablename__ = "seat_change_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer,ForeignKey("students.id"),nullable=False)
    current_allocation_id = Column(Integer,ForeignKey("seat_allocations.id"),nullable=False)
    requested_seat_id = Column(Integer,ForeignKey("seats.id"),nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(20),nullable=False,default="Pending")
    approved_by = Column(Integer,ForeignKey("users.id"),nullable=True)

    student = relationship("Student", back_populates="seat_change_requests")
    current_allocation = relationship("Seat_Allocations", back_populates="change_requests", foreign_keys=[current_allocation_id])
    requested_seat = relationship("Seats", back_populates="change_requests", foreign_keys=[requested_seat_id])
    approver = relationship("Users", foreign_keys=[approved_by])

class Libraries(Base):
    __tablename__ = 'libraries'

    id = Column(Integer,primary_key=True, nullable=False)
    name = Column(String(50),unique=True,nullable=False)
    address= Column(String(50),nullable=False)
    email = Column(String(100),nullable=False,unique=True)
    phone = Column(String(20),nullable=False,unique=True)
    status= Column(String)

    settings = relationship("Library_Setting", back_populates="library", uselist=False)
    memberships = relationship("Library_Memberships", back_populates="library")
    students = relationship("Student", back_populates="library")
    shifts = relationship("Shifts", back_populates="library")
    seats = relationship("Seats", back_populates="library")
    subscriptions = relationship("Subscriptions", back_populates="library")
    payments = relationship("Payment", back_populates="library")
    announcements = relationship("Announcements", back_populates="library")

class Subscriptions(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer,primary_key=True,nullable=False)
    library_id = Column(Integer,ForeignKey('libraries.id'))
    plan_name = Column(String)
    amount = Column(Numeric)
    start_date = Column(Date,nullable=False)
    end_date = Column(Date)
    status = Column(String)

    library = relationship("Libraries", back_populates="subscriptions")

class Library_Setting(Base):
    __tablename__='library_settings'


    id = Column(Integer,primary_key=True,nullable=False)
    library_id = Column(Integer,ForeignKey('libraries.id'))
    currency = Column(String,nullable=False)
    timezone = Column(String)
    default_monthly_fee = Column(Numeric)
    allow_online_payment= Column(Boolean,default=True)
    allow_seat_change = Column(Boolean,default=True)
    max_shift_per_student = Column(Integer)

    library = relationship("Libraries", back_populates="settings")

class Shifts(Base):
    __tablename__='shifts'

    id = Column(Integer,primary_key=True)
    library_id = Column(Integer,ForeignKey('libraries.id'))
    name = Column(String)
    start_time = Column(DateTime,default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String)
    
    library = relationship("Libraries", back_populates="shifts")
    student_shifts = relationship("Student_Shifts", back_populates="shift")

class Student_Shifts(Base):
    __tablename__ = 'student_shifts'

    id = Column(Integer,primary_key=True,nullable=False)
    student_id = Column(Integer,ForeignKey('students.id'))
    shift_id = Column(Integer, ForeignKey('shifts.id'))
    joined_on = Column(Date)
    status = Column(String)

    student = relationship("Student", back_populates="student_shifts")
    shift = relationship("Shifts", back_populates="student_shifts")
    seat_allocations = relationship("Seat_Allocations", back_populates="student_shift")

class Seats(Base):
    __tablename__ = 'seats'

    id = Column(Integer,primary_key=True,nullable=False)
    library_id = Column(Integer,ForeignKey('libraries.id'))
    seat_number = Column(String)
    seat_type = Column(String)
    status = Column(String)

    library = relationship("Libraries", back_populates="seats")
    allocations = relationship("Seat_Allocations", back_populates="seat")
    change_requests = relationship("SeatChangeRequest", back_populates="requested_seat", foreign_keys="SeatChangeRequest.requested_seat_id")

class Seat_Allocations(Base): 
    __tablename__ = 'seat_allocations'

    id = Column(Integer,primary_key=True,nullable=False)
    student_shift_id = Column(Integer,ForeignKey('student_shifts.id'))
    seat_id = Column(Integer, ForeignKey('seats.id')) 
    allocated_on = Column(Date)
    ended_on = Column(Date,nullable = True)
    status = Column(String)

    student_shift = relationship("Student_Shifts", back_populates="seat_allocations")
    seat = relationship("Seats", back_populates="allocations")
    change_requests = relationship(
        "SeatChangeRequest", back_populates="current_allocation",
        foreign_keys="SeatChangeRequest.current_allocation_id")
