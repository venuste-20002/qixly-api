from statistics import mean
from uuid import UUID

from sqlmodel import Session

from src.models.card_model import Card
from src.models.reviews_model import Reviews
from src.models.sales_model import SalesItem
from src.schemas.review_schema import ReviewResponseSchema, ReviewsSchema
from src.utils.fetcher import Fetcher


class ReviewController:
    def __init__(self, database: Session, card_id: UUID):
        self.database = database
        self.card_id = card_id

    async def get_card(self):
        is_get_reviews = Fetcher(
            database=self.database,
            table=(Card,),
            where=(Card.id == self.card_id,),
            error="No card found",
        ).get_one()

        return is_get_reviews

    async def get_all_reviews(self):
        await self.get_card()

        get_reviews = Fetcher(
            database=self.database,
            table=(Reviews,),
            where=(Reviews.card_id == self.card_id,),
            error="No reviews found",
        ).get_all()

        return get_reviews

    async def get_review(self, user_id: UUID):
        is_check_reviewd = Fetcher(
            database=self.database,
            table=(Reviews,),
            where=(
                Reviews.card_id == self.card_id,
                Reviews.user_id == user_id,
            ),
        ).get_value()

        return is_check_reviewd

    async def get_review_average(self):
        await self.get_card()
        get_review = await self.get_all_reviews()
        average_rating = mean(map(lambda x: x.rating, get_review))
        return average_rating

    async def add_post_review(self, input_data: ReviewsSchema):
        await self.get_card()

        Fetcher(
            database=self.database,
            table=(SalesItem,),
            where=(
                SalesItem.card_id == self.card_id,
                SalesItem.user_id == input_data.user_id,
            ),
            error="Unable to review on this card, you need to buy this card first",
        ).get_one()

        is_check_review = await self.get_review(input_data.user_id)

        if is_check_review:
            updated_review = input_data.model_dump(
                exclude_none=True, exclude_unset=True
            )
            is_check_review.sqlmodel_update(updated_review)

            self.database.commit()
            self.database.refresh(is_check_review)
            return ReviewResponseSchema(**is_check_review.model_dump())

        add_review = Reviews(**input_data.model_dump())

        self.database.add(add_review)
        self.database.commit()
        self.database.refresh(add_review)

        return ReviewResponseSchema(**add_review.model_dump())
