import base64
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.utils import formataddr
# import pyotp
import pyotp
from fastapi import status

from src.config import settings
from src.utils.custom_errors import AppError


class Mailer:
    def __init__(self, to_address: str):
        self.to_address = to_address

    async def mailer_config(
        self,
        message: str,
        subject: str = "Notification",
    ):
        email = EmailMessage()
        email["From"] = formataddr(("Your App Name", settings.MAILER_EMAIL))
        email["To"] = self.to_address
        email["Subject"] = subject
        email.set_content(message)

        try:
            with smtplib.SMTP(settings.MAILER_SERVER, settings.MAILER_PORT) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(settings.MAILER_EMAIL, settings.MAILER_PASSWORD)
                smtp.send_message(email)
        except Exception as e:
            raise AppError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {str(e)}",
            )

    async def reset_password(self, token: str):
        message = f"""\
            Hello,

            Reset Password Link: {token}
        """
        await self.mailer_config(message, subject="Reset Password")

        # kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk

    async def verification_email(self, secret: str):
        totp = pyotp.TOTP(secret, interval=120)
        token = totp.now()
        message = f"""\
        Hello,

        Verification Email: {token}
        """
        await self.mailer_config(message, subject="Email Verification")

        # hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh

    # async def verification_email(self, link: str):
    #     message = f"""\
    #     Hello,

    #     Verification Email: {link}
    #     """
    #     await self.mailer_config(message, subject="Email Verification")

        # hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh

    async def share_email(self, qrcode, cost: int):
        qrcode = base64.b64encode(qrcode.getvalue()).decode()
        # TODO: the images are not displaying in the email

        message = f"""\
            <html>
                <body>
                    <p>Hello,</p>
                    <p>The sales item with a card amount of <strong>{cost} RWF</strong> has been successfully shared with you.</p>
                    <p>Scan the QR code below for more details:</p>
                    <img src="data:image/png;base64,{qrcode}" alt="QR Code" />
                    <p>Thank you!</p>
                </body>
            </html>
            """

        message_send = MIMEText(message, "html")

        await self.mailer_config(message_send, subject="Share Email")
