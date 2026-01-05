from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from src.controllers.review_controller import ReviewController
from src.database import database
from src.middlewares.auth import auth
from src.schemas.card_schema import CardResponse
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.review_schema import (
    ReviewFullResponseSchema,
    ReviewResponseSchema,
    ReviewsInputSchema,
    ReviewsSchema,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"], dependencies=[Depends(auth)])


@router.post(
    "/me",
    status_code=201,
    response_model=CommonResponseSchema[ReviewResponseSchema],
)
async def adding_new_review(
    request: Request, db: database, input_data: ReviewsInputSchema
):
    user_id = request.session["user"]["id"]
    add_review = await ReviewController(
        database=db,
        card_id=input_data.card_id,
    ).add_post_review(
        input_data=ReviewsSchema(
            **input_data.model_dump(),
            user_id=user_id,
        ),
    )
    return CommonResponseSchema(
        message="Review added successfully",
        data=add_review,
    )


@router.get(
    "/{card_id}",
    status_code=200,
    response_model=CommonResponseSchema[List[ReviewFullResponseSchema]],
)
async def get_card_reviews(_: Request, card_id: UUID, db: database):

    get_all_reviews = await ReviewController(
        database=db, card_id=card_id
    ).get_all_reviews()

    return CommonResponseSchema(
        message="Reviews fetched successfully",
        data=[
            ReviewFullResponseSchema(
                **review.model_dump(),
                card=CardResponse(**review.card.model_dump()),
            )
            for review in get_all_reviews
        ],
    )


@router.get(
    "/{card_id}/average",
    status_code=200,
    response_model=CommonResponseSchema,
)
async def get_card_average_rating(card_id: UUID, _: Request, db: database):
    get_review_average = await ReviewController(
        database=db, card_id=card_id
    ).get_review_average()
    return CommonResponseSchema(
        message="Average rating fetched successfully",
        data={
            "card_id": card_id,
            "average": get_review_average,
        },
    )
