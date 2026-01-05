from uuid import UUID

from sqlmodel import SQLModel


class PermissionResponse(SQLModel):
    id: UUID
    name: str
    group: str
    description: str
