from sqlmodel import Session, select

from src.models.authentication_model import Permissions


class PermissionController:
    def __init__(self, database: Session) -> None:
        self.database = database

    def get_permission_groups(self):
        query_get_all_permissions = self.database.exec(
            select(Permissions).where(getattr(Permissions, "is_deleted") == False)
        ).all()

        get_permission_groups: list = list(
            set(permission.group for permission in query_get_all_permissions)
        )

        return get_permission_groups
