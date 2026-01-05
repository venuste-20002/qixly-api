from hmac import compare_digest

from fastapi import status

from src.models.authentication_model import Users
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch
from src.utils.password_encrypt import compare_password, hash_password


class ResetPasswordController:
    def __init__(self, email, old_password, new_password, database):
        self.email = email
        self.old_password = old_password
        self.new_password = new_password
        self.database = database

    async def check_old_password(self):
        get_user = Fetch(Users, "email", self.email, self.database)
        get_user_details = await get_user.get_single_value()

        if not get_user_details:
            raise AppError(
                detail="{self.email} does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if not compare_password(self.old_password, get_user_details.password):
            raise AppError(
                detail="Wrong old password", status_code=status.HTTP_409_CONFLICT
            )

        if compare_digest(self.old_password, self.new_password):
            raise AppError(
                detail="New password cannot be same as old password",
            )

        return get_user_details

    async def __call__(self):
        new_user_details = await self.check_old_password()
        new_password_hashed = hash_password(self.new_password)

        new_user_details.password = new_password_hashed

        self.database.add(new_user_details)
        self.database.commit()
        return "Password successfully updated"
