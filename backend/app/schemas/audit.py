from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum


class AuditActionEnum(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    IMPERSONATE_START = "impersonate_start"
    IMPERSONATE_END = "impersonate_end"
    EXPORT = "export"


class AuditLogBase(BaseModel):
    action: AuditActionEnum
    entity_type: str
    entity_id: Optional[int] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    description: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    user_id: int


class AuditLog(AuditLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[AuditActionEnum] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
