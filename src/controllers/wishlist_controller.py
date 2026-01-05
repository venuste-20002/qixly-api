from typing import Optional
from uuid import UUID

from fastapi import status
from sqlmodel import Session, select

from src.models.card_model import Card
from src.models.wishlist_model import Wishlist
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch


class WishlistController:
    def __init__(
        self,
        database: Session,
        user_uuid: UUID,
        card_id: Optional[UUID] = None,
    ) -> None:
        self.database = database
        self.user_uuid = user_uuid
        self.card_id = card_id

    async def get_wishlist(self):
        query_get_user_wishlist = await Fetch(
            Wishlist, "user_id", self.user_uuid,self.database
        ).get_all_value()

        if not query_get_user_wishlist:
            query_get_user_wishlist = []

        return query_get_user_wishlist

    async def get_card(self):
        query_get_card = await Fetch(Card, "id", self.card_id,self.database).get_single_value()

        if not query_get_card:
            raise AppError("Card not found", status.HTTP_404_NOT_FOUND)

        return query_get_card

    async def add_to_wishlist(self):
        await self.get_card()

        is_check_if_item_exist = (
            select(Wishlist)
            .where(Wishlist.card_id == self.card_id)
            .where(Wishlist.user_id == self.user_uuid)
            .where(Wishlist.is_deleted == False)
        )

        get_wishlist_items = self.database.exec(is_check_if_item_exist).first()
        if get_wishlist_items:
            raise AppError(
                "Item already exist in wishlist",
            )

        add_card_item_to_wishlist = Wishlist(
            user_id=self.user_uuid,
            card_id=self.card_id,
        )

        self.database.add(add_card_item_to_wishlist)
        self.database.commit()
        self.database.refresh(add_card_item_to_wishlist)

        return add_card_item_to_wishlist

    async def delete_single_wishlist(self, wishlist_id: UUID):
        get_wishlist_items = await Fetch(
            Wishlist,
            "id",
            wishlist_id,
            self.database
        ).get_single_value()
        if not get_wishlist_items:
            raise AppError("Wishlist item not found", status.HTTP_404_NOT_FOUND)

        self.database.delete(get_wishlist_items)
        self.database.commit()

        return {"message": "Wishlist item deleted successfully"}

    async def delete_wishlist(self):
        get_wishlist_items = await self.get_wishlist()

        if not get_wishlist_items:
            raise AppError("Wishlist item not found", status.HTTP_404_NOT_FOUND)

        for item in get_wishlist_items:
            self.database.delete(item)

        self.database.commit()

        return get_wishlist_items
