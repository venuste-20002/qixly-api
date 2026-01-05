from sqlmodel import Field, Relationship

from src.models.common_base import CommonBase



class Category(CommonBase, table=True):
    name: str = Field(unique=True, nullable=False, index=True)
    description: str = Field(default=None, nullable=True)

    cards: list["Card"] = Relationship(back_populates="category")

    @staticmethod
    def searchable_fields():
        return [Category.name]
