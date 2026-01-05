
import requests
from fastapi import status
from uuid import UUID
from src.utils.custom_errors import AppError
from src.config import settings
import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

SMS_URL = settings.SMS_API_URL
SMS_API_KEY = settings.SMS_API_KEY_PUSH
SMS_SENDER = "Nokanda"
SMS_API_TOKEN = settings.SMS_API_TOKEN

async def send_sms(to: str, text: str):
    """
    Sends an SMS using the SMS API.

    Args:
        to (str): The recipient's phone number.
        text (str): The message content.

    Returns:
        dict: The response from the SMS API.

    Raises:
        AppError: If the SMS fails to send.
    """
    headers = {
        "Authorization": f"Bearer {SMS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "sender": SMS_SENDER,
        "external_id": str(UUID), 
        "callbacks": [],
        "to": [to]
    }

    response = requests.post(SMS_URL, json=payload, headers=headers)
    if response.status_code != 200:
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send SMS"
        )
    return response.json()
