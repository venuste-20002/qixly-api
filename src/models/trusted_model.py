from sqlmodel import Field

from src.models.common_base import CommonBase


class Trusted(CommonBase, table=True):
    name: str = Field(default=None, nullable=True)
    public_key: str = Field(default=None, nullable=True)
    private_key: str = Field(default=None, nullable=True)
    is_active: bool = Field(default=True, nullable=False)
