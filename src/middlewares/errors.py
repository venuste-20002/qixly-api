import traceback

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.schemas.common_schema import CommonResponseSchema
from src.utils.logger import logger


def get_all_errors():
    async def handle_middleware(req: Request, call_next):
        try:
            forwarded = req.headers.get("X-Forwarded-For")
            if forwarded:
                logger.info(
                    "Request from {}:{}:{}".format(
                        forwarded, req.client, req.scope["path"]
                    )
                )
                return await call_next(req)
            logger.info("Request from {}:{}".format(req.client, req.scope["path"]))

            return await call_next(req)
        except Exception as e:
            logger.error(f"Unhandled error: {e}")

            error_response = CommonResponseSchema(
                message=f"{str(e)}",
                status="error",
                data=jsonable_encoder(traceback.format_exc().split("\n")[-10:]),
            ).model_dump()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response,
            )

    return handle_middleware
