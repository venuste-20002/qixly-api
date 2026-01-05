from enum import Enum

from sqlmodel import Session, select

from src.database import engine
from src.models.authentication_model import Permissions


class PermissionGroup(str, Enum):
    SYSTEM = "SYSTEM"
    INSTITUTION = "INSTITUTION"
    BRANCH = "BRANCH"
    BASIC = "BASIC"

    def __init__(self, group):
        self.group = group

    def __str__(self) -> str:
        return f"{self.group}"


class PermissionActivity(str, Enum):
    WRITE = "WRITE"
    READ = "READ"
    DELETE = "DELETE"

    def __init__(self, activity):
        self.activity = activity

    def __str__(self) -> str:
        return f"{self.activity}"


class PermissionsResources(Enum):
    USER = ("USER", PermissionGroup.BASIC)
    USERS = ("USERS", PermissionGroup.SYSTEM)
    ROLES = ("ROLES", PermissionGroup.SYSTEM)
    INSTITUTIONS = ("INSTITUTIONS", PermissionGroup.SYSTEM)
    INSTITUTION = ("INSTITUTION", PermissionGroup.INSTITUTION)
    USERSCOPES = ("USERSCOPES", PermissionGroup.SYSTEM)
    BRANCHES = ("BRANCHES", PermissionGroup.BRANCH)
    MEMBERS = ("MEMBERS", PermissionGroup.INSTITUTION)
    WISHLIST = ("WISHLIST", PermissionGroup.BASIC)
    PERMISSIONS = ("PERMISSIONS", PermissionGroup.SYSTEM)
    CLAIM = ("CLAIM", PermissionGroup.INSTITUTION)
    CART = ("CART", PermissionGroup.BASIC)
    CARTS = ("CARTS", PermissionGroup.SYSTEM)
    SALE = ("SALE", PermissionGroup.BASIC)
    SALES = ("SALES", PermissionGroup.SYSTEM)
    CARDS = ("CARDS", PermissionGroup.SYSTEM)
    CARD = ("CARD", PermissionGroup.INSTITUTION)

    def __init__(
        self,
        permission_resource: str,
        permission_group: PermissionGroup,
    ):
        self.permission_resource = permission_resource
        self.permission_group = permission_group

    def __str__(self) -> str:
        return f"{self.permission_resource}"


def permission__(
    permission_resource: PermissionsResources, permission_activity: PermissionActivity
):
    return f"{permission_resource.permission_resource}:{permission_activity.value}"


async def seed_permissions():
    with Session(engine) as session:
        get_all_permissions = session.exec(select(Permissions)).all()
        current_permission = {permission.name for permission in get_all_permissions}
        keep_permissions = set()

        for resource in PermissionsResources:
            for activity in PermissionActivity:
                keep_permissions.add(
                    permission__(
                        permission_resource=PermissionsResources[
                            resource.permission_resource
                        ],
                        permission_activity=PermissionActivity[activity],
                    )
                )

        for permission in keep_permissions - current_permission:
            resource, activity = permission.split(":")
            group = PermissionsResources[resource].permission_group.value
            session.add(
                Permissions(
                    name=permission,
                    group=group,
                    description="Permission",
                )
            )
        for permission in current_permission - keep_permissions:
            permission_to_remove = session.exec(
                select(Permissions).where(getattr(Permissions, "name") == permission)
            ).first()
            if permission_to_remove:
                session.delete(permission_to_remove)

        session.commit()
