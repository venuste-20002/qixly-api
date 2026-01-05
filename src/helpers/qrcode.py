import io

import qrcode


async def qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )

    qr.add_data(data)
    qr.make(fit=True)
    create_token = qr.make_image(fill_color="black", back_color="white")

    buffered = io.BytesIO()
    create_token.save(buffered, format="PNG")
    buffered.seek(0)

    return buffered
