from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.public import TenantStatus

# 基础模型
class AdmissionBatchBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_active: bool = False
    description: Optional[str] = None

class DepartmentBase(BaseModel):
    name: str
    code: Optional[str] = None
    parent_id: Optional[int] = None
    order: int = 0
    leader: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: bool = True

class StudentBase(BaseModel):
    id_card: str
    student_id: str
    name: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    admission_batch_id: Optional[int] = None
    department_id: Optional[int] = None
    dormitory_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: bool = True
    ext_field1: Optional[str] = None
    ext_field2: Optional[str] = None
    ext_field3: Optional[str] = None
    ext_field4: Optional[str] = None
    ext_field5: Optional[str] = None
    ext_field6: Optional[str] = None
    ext_field7: Optional[str] = None
    ext_field8: Optional[str] = None
    ext_field9: Optional[str] = None
    ext_field10: Optional[str] = None

class DormitoryBase(BaseModel):
    building: str
    room_number: str
    capacity: int = 4
    current_count: int = 0
    status: bool = True

class StaffBase(BaseModel):
    username: str
    password: str
    name: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    status: bool = True

class RegistrationProcessBase(BaseModel):
    name: str
    order: int
    description: Optional[str] = None
    is_required: bool = True
    status: bool = True

class InfoEntryProcessBase(BaseModel):
    name: str
    order: int
    description: Optional[str] = None
    is_required: bool = True
    status: bool = True

class RegistrationInfoBase(BaseModel):
    student_id: str
    process_id: int
    status: bool = False
    completed_at: Optional[datetime] = None
    operator_id: Optional[int] = None
    remarks: Optional[str] = None

class FieldMappingBase(BaseModel):
    field_name: str
    display_name: str
    is_required: bool = False
    order: int = 0
    status: bool = True

# 创建模型
class AdmissionBatchCreate(AdmissionBatchBase):
    pass

class DepartmentCreate(DepartmentBase):
    pass

class StudentCreate(StudentBase):
    pass

class DormitoryCreate(DormitoryBase):
    pass

class StaffCreate(StaffBase):
    pass

class RegistrationProcessCreate(RegistrationProcessBase):
    pass

class RegistrationInfoCreate(RegistrationInfoBase):
    pass

class FieldMappingCreate(FieldMappingBase):
    pass

# 更新模型
class AdmissionBatchUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[int] = None
    order: Optional[int] = None
    leader: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[bool] = None

class StudentUpdate(BaseModel):
    student_id: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    admission_batch_id: Optional[int] = None
    department_id: Optional[int] = None
    dormitory_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: Optional[bool] = None
    ext_field1: Optional[str] = None
    ext_field2: Optional[str] = None
    ext_field3: Optional[str] = None
    ext_field4: Optional[str] = None
    ext_field5: Optional[str] = None
    ext_field6: Optional[str] = None
    ext_field7: Optional[str] = None
    ext_field8: Optional[str] = None
    ext_field9: Optional[str] = None
    ext_field10: Optional[str] = None

class DormitoryUpdate(BaseModel):
    building: Optional[str] = None
    room_number: Optional[str] = None
    capacity: Optional[int] = None
    current_count: Optional[int] = None
    status: Optional[bool] = None

class StaffUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    status: Optional[bool] = None

class RegistrationProcessUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    status: Optional[bool] = None

class RegistrationInfoUpdate(BaseModel):
    student_id: Optional[str] = None
    process_id: Optional[int] = None
    status: Optional[bool] = None
    completed_at: Optional[datetime] = None
    operator_id: Optional[int] = None
    remarks: Optional[str] = None

class FieldMappingUpdate(BaseModel):
    field_name: Optional[str] = None
    display_name: Optional[str] = None
    is_required: Optional[bool] = None
    order: Optional[int] = None
    status: Optional[bool] = None

# 响应模型
class AdmissionBatchResponse(AdmissionBatchBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudentResponse(StudentBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DormitoryResponse(DormitoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StaffResponse(StaffBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RegistrationProcessResponse(RegistrationProcessBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RegistrationInfoResponse(RegistrationInfoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FieldMappingResponse(FieldMappingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TenantBase(BaseModel):
    name: str = Field(..., description="租户名称")
    description: Optional[str] = Field(None, description="租户描述")
    max_users: Optional[int] = Field(100, description="最大用户数")
    expire_date: Optional[date] = Field(None, description="过期日期")

class TenantCreate(TenantBase):
    pass

class TenantUpdate(TenantBase):
    status: Optional[TenantStatus] = Field(None, description="租户状态")

class TenantResponse(TenantBase):
    id: int
    schema_name: str
    status: TenantStatus
    is_deleted: bool

    class Config:
        from_attributes = True 