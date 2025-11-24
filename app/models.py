#from enum import unique
import enum
from pickle import TRUE
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP, TIME, DATE
from .database import Base
from sqlalchemy import Column, Integer, Boolean,String, Float, JSON, Text,Date,Enum,UniqueConstraint
from sqlalchemy.sql import func

from datetime import date
from typing import List, Optional



class Employee(Base):
    __tablename__ = 'employees'

    # The table has a UNIQUE constraint on full_name,
    # and a self-referential FOREIGN KEY constraint.

    # ----------------------------------------------------
    # Columns derived from the CREATE TABLE statement:
    # ----------------------------------------------------

    # employee_id integer NOT NULL DEFAULT nextval(...)
    # SQLAlchemy handles the sequence for an Integer primary key automatically
    employee_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # full_name character varying(100) NOT NULL, CONSTRAINT employees_full_name_key UNIQUE (full_name)
    full_name: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)

    user_name :  Mapped[str] = mapped_column(String(100), unique=True, nullable=False,)

    password : Mapped[str] = mapped_column(String(100), nullable=False, default="test")


    # department character varying(50)
    department: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # hire_date date
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # manager_employee_id integer, CONSTRAINT manager_id_foreign_key FOREIGN KEY (manager_employee_id) REFERENCES public.employees (employee_id)
    manager_employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('employees.employee_id'),
        nullable=True # Since no NOT NULL is specified
    )

    # role character varying
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True)


    # ----------------------------------------------------
    # Self-Referential Relationships:
    # ----------------------------------------------------

    # Relationship to the Manager (Many-to-One):
    # This represents the single manager for the current employee.
    manager: Mapped[Optional["Employee"]] = relationship(
        back_populates="subordinates",
        remote_side=[employee_id], # 'employee_id' is the primary key column on the 'remote' side (the manager record)
    )

    # Relationship to Subordinates (One-to-Many):
    # This represents the list of employees who report to the current employee.
    subordinates: Mapped[List["Employee"]] = relationship(
        back_populates="manager",
        # The 'foreign_keys' argument is often needed for self-referential many-to-one/one-to-many,
        # but SQLAlchemy can usually infer it correctly when the FK is defined on the mapped_column.
        # We explicitly rely on the ForeignKey on manager_employee_id.
    )

    # Relationship to LeaveTransaction (One-to-Many):
    leave_transactions: Mapped[List["LeaveTransaction"]] = relationship(
         back_populates="employee"
     )
    

    def __repr__(self) -> str:
        return (
            f"Employee(id={self.employee_id!r}, name={self.full_name!r}, "
            f"dept={self.department!r}, manager_id={self.manager_employee_id!r})"
        )
    


class LeaveType(enum.Enum):
    #"""Corresponds to the leave_type_enum in PostgreSQL."""
    general = "general"
    sick = "sick"
    casual = 'casual'
    vacation = "vacation"
    maternity = "maternity"
    paternity  = "paternity"
    bereavement = "bereavement"
    # Add other leave types as needed

class LeaveStatus(enum.Enum):
    """Corresponds to the leave_status_enum in PostgreSQL."""
    Applied = "Applied"
    Approved = "Approved"
    Rejected = "Rejected"
    # Add other statuses as needed


class MaxLeaveQuota(Base):
    __tablename__ = 'max_leave_quota'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType, name='leave_type_enum', create_type=TRUE), # create_type=False assumes the ENUM type exists in the DB
        nullable=False,
    )
    max_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=False)



# 2. Define the LeaveTransaction Model
class LeaveTransaction(Base):
    __tablename__ = 'leave_transactions'

    # The table has a composite UNIQUE constraint on (employee_id, leave_date).

    # ----------------------------------------------------
    # Table Constraints (Composite Unique Constraint):
    # ----------------------------------------------------
    __table_args__ = (
        UniqueConstraint('employee_id', 'leave_date', name='leave_transactions_employee_id_leave_date_key'),
    )

    # ----------------------------------------------------
    # Columns derived from the CREATE TABLE statement:
    # ----------------------------------------------------

    # transaction_id integer NOT NULL DEFAULT nextval(...)
    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # employee_id integer NOT NULL, CONSTRAINT fk_employee FOREIGN KEY (employee_id) REFERENCES public.employees (employee_id)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey('employees.employee_id'),
        nullable=False
    )

    # leave_date date NOT NULL
    leave_date: Mapped[date] = mapped_column(Date, nullable=False)

    # leave_type leave_type_enum NOT NULL DEFAULT 'General Leave'::leave_type_enum
    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType, name='leave_type_enum', create_type=TRUE), # create_type=False assumes the ENUM type exists in the DB
        #String(100),
        nullable=False,
        default=LeaveType.general
    )

    # leave_status leave_status_enum NOT NULL DEFAULT 'Applied'::leave_status_enum
    leave_status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus, name='leave_status_enum', create_type=True), # create_type=False assumes the ENUM type exists in the DB
        #String(100),
        nullable=False,
        default=LeaveStatus.Applied
    )


    # ----------------------------------------------------
    # Relationship to Employee:
    # ----------------------------------------------------

    # Relationship back to the Employee model (assuming 'Employee' is defined elsewhere)
    # The 'employee' attribute provides access to the employee who took the leave.
    employee: Mapped["Employee"] = relationship(back_populates="leave_transactions")

    def __repr__(self) -> str:
        return (
            f"LeaveTransaction(id={self.transaction_id!r}, employee_id={self.employee_id!r}, "
            f"date={self.leave_date!r}, type={self.leave_type.value!r}, status={self.leave_status.value!r})"
        )
    


# 1. Define Python Enum for Permissions
class Permission(enum.Enum):
    """Corresponds to the permission_enum in PostgreSQL."""
    SELF_READ = "SELF_READ"
    ALL_READ = "ALL_READ"
    SELF_LEAVE_APPLY = "SELF_LEAVE_APPLY"
    # Add other permissions as needed

# 2. Define the EmployeePermission Association Model
class EmployeePermission(Base):
    __tablename__ = 'employee_permissions'

    # The table has a composite PRIMARY KEY and UNIQUE constraint on (employee_id, permission).
    __table_args__ = (
        UniqueConstraint('employee_id', 'permission', name='unique_employee_permission'),
        # Note: The composite primary key is defined implicitly by setting both
        # employee_id and permission as primary_key=True below.
    )

    # ----------------------------------------------------
    # Columns derived from the CREATE TABLE statement:
    # ----------------------------------------------------

    # employee_id integer NOT NULL, FOREIGN KEY
    employee_id: Mapped[int] = mapped_column(
        ForeignKey('employees.employee_id', ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True
    )

    # permission permission_enum NOT NULL
    permission: Mapped[Permission] = mapped_column(
        Enum(Permission, name='permission_enum', create_type=True),
        primary_key=True,
        nullable=False
    )

    # ----------------------------------------------------
    # Relationships (Optional, but often useful for association tables):
    # ----------------------------------------------------

    # Relationship to the Employee model (back-reference to the Employee instance)---uncomment next line if relation added to Emplyee model also
    #employee: Mapped["Employee"] = relationship(back_populates="permissions_links")

    def __repr__(self) -> str:
        return (
            f"EmployeePermission(employee_id={self.employee_id!r}, "
            f"permission={self.permission.value!r})"
        )
    


class Policy(Base):
    __tablename__ = 'company_policy'

    # ----------------------------------------------------
    # Columns:
    # ----------------------------------------------------

    # id: primary key, integer
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # policy_type: non-nullable string (e.g., VARCHAR(50))
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # policy_details: string (allowing longer text, using general String or Text)
    # Assuming nullable, as policy details can sometimes be optional or short
    policy_details: Mapped[Optional[str]] = mapped_column(String, nullable=True)


    def __repr__(self) -> str:
        return (
            f"Policy(id={self.id!r}, type={self.policy_type!r}, "
            f"details_length={len(self.policy_details or '')})"
        )