from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Text
from .base import BaseModel

class AdmissionBatch(BaseModel):
    __tablename__ = "admission_batches"
    
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False)
    description = Column(String(500))

class Department(BaseModel):
    __tablename__ = "departments"
    
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True)
    parent_id = Column(Integer)
    order = Column(Integer, default=0)
    leader = Column(String(50))
    phone = Column(String(20))
    email = Column(String(100))
    status = Column(Boolean, default=True)

class Student(BaseModel):
    __tablename__ = "students"
    
    id_card = Column(String(18), primary_key=True)
    student_id = Column(String(50), unique=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(10))
    birth_date = Column(Date)
    admission_batch_id = Column(Integer)
    department_id = Column(Integer)
    dormitory_id = Column(Integer)
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String(200))
    status = Column(Boolean, default=True)
    # 预留10个扩展字段
    ext_field1 = Column(String(200))
    ext_field2 = Column(String(200))
    ext_field3 = Column(String(200))
    ext_field4 = Column(String(200))
    ext_field5 = Column(String(200))
    ext_field6 = Column(String(200))
    ext_field7 = Column(String(200))
    ext_field8 = Column(String(200))
    ext_field9 = Column(String(200))
    ext_field10 = Column(String(200))

class Dormitory(BaseModel):
    __tablename__ = "dormitories"
    
    building = Column(String(50), nullable=False)
    room_number = Column(String(20), nullable=False)
    capacity = Column(Integer, default=4)
    current_count = Column(Integer, default=0)
    status = Column(Boolean, default=True)

class Staff(BaseModel):
    __tablename__ = "staff"
    
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    name = Column(String(50), nullable=False)
    gender = Column(String(10))
    phone = Column(String(20))
    email = Column(String(100))
    department_id = Column(Integer)
    position = Column(String(50))
    status = Column(Boolean, default=True)

class RegistrationProcess(BaseModel):
    __tablename__ = "registration_processes"
    
    name = Column(String(100), nullable=False, unique=True)
    order = Column(Integer, nullable=False)
    description = Column(String(500))
    is_required = Column(Boolean, default=True)
    status = Column(Boolean, default=True)

class InfoEntryProcess(BaseModel):
    __tablename__ = "info_entry_processes"
    
    name = Column(String(100), nullable=False, unique=True)
    order = Column(Integer, nullable=False)
    description = Column(String(500))
    is_required = Column(Boolean, default=True)
    status = Column(Boolean, default=True)

class RegistrationInfo(BaseModel):
    __tablename__ = "registration_info"
    
    student_id = Column(String(50), nullable=False)
    process_id = Column(Integer, nullable=False)
    status = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    operator_id = Column(Integer)
    remarks = Column(Text)

class FieldMapping(BaseModel):
    __tablename__ = "field_mappings"
    
    field_name = Column(String(50), nullable=False)
    display_name = Column(String(50), nullable=False)
    is_required = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    status = Column(Boolean, default=True) 