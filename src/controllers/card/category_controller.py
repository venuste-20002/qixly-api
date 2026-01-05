from uuid import UUID

from sqlmodel import Session, select

from src.models.card_model import Category
from src.schemas.card_schema import CategorySchemas
from src.utils.custom_errors import AppError


def create_category(category_data: CategorySchemas, db: Session):
    statement = select(Category).where(Category.name == category_data.name)
    existing_category = db.exec(statement).first()
    if existing_category:
        raise AppError(status_code=400, detail="Category already exists")

    new_category = Category(
        name=category_data.name, description=category_data.description
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


def get_category_by_id(category_id: UUID, db: Session):
    statement = select(Category).where(Category.id == category_id)
    category = db.exec(statement).first()
    if not category:
        raise AppError(status_code=404, detail="Category not found")
    return category


def update_category(category_id: UUID, category_data: CategorySchemas, db: Session):
    statement = select(Category).where(Category.id == category_id)
    category = db.exec(statement).first()
    if category is None:
        raise AppError(status_code=404, detail="Category not found")

    category.name = category_data.name
    category.description = category_data.description
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
