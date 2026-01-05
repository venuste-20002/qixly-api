from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class CommonBase(SQLModel):
    id: UUID = Field(
        default_factory=uuid4, primary_key=True, unique=True, nullable=False
    )
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    is_deleted: bool = Field(default=False, nullable=True)

    @staticmethod
    def searchable_fields():
        return []
