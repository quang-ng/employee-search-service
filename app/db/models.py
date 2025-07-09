from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Index

Base = declarative_base()

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    # Configurable fields for employee directory (as JSON array of field names)
    employee_fields = Column(JSON, nullable=False, default=list)
    employees = relationship('Employee', back_populates='organization')

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    name = Column(String, nullable=False)
    department = Column(String)
    location = Column(String)
    position = Column(String)
    contact_info = Column(String)
    status = Column(String)  # e.g., 'active', 'inactive', etc.
    company = Column(String) # e.g., for multi-company orgs
    organization = relationship('Organization', back_populates='employees')

    __table_args__ = (
        Index('idx_employees_org_id', 'org_id'),
        Index('idx_employees_status', 'status'),
        Index('idx_employees_location', 'location'),
        Index('idx_employees_company', 'company'),
        Index('idx_employees_department', 'department'),
        Index('idx_employees_position', 'position'),
    )

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    organization = relationship('Organization') 