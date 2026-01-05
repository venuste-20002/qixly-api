from datetime import datetime
from io import BytesIO
from typing import Optional

from fastapi import Response
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, PageTemplate, SimpleDocTemplate

from src.helpers.report_formatter import (
    Alignment,
    RColumn,
    RKeyValue,
    RParagraph,
    RQRCode,
    RRow,
    get_font_name,
)
from src.schemas.sales_schema import SalesItemFullSchema


def format_price(price: int):
    return "{:,}".format(price)


def format_reciept_date(date: datetime):
    return date.strftime("%d %b %Y, %I:%M %p")


def add_background(canvas: canvas.Canvas, doc):
    canvas.saveState()
    canvas.drawImage(
        "resources/images/icon.png",
        x=250,
        y=480,
        width=80,
        height=80,
        preserveAspectRatio=True,
        mask="auto",
    )
    canvas.restoreState()


def generate_sales_item_pdf(
    res: SalesItemFullSchema,
    file_name: Optional[str] = None,
):
    data = [
        RRow(
            [
                RColumn(
                    data=[
                        RParagraph(
                            text=f"{res.card.name}", alignment=TA_LEFT, font_size=25
                        ),
                        RParagraph(
                            f"By: {res.card.institution.name}",
                            alignment=TA_LEFT,
                            font_size=12,
                        ),
                    ],
                    p_bottom=20,
                ),
            ]
        ),
        RRow(
            [
                RColumn(
                    [
                        RKeyValue(
                            {
                                "Price:": f"{res.card_variant.price} RWF",
                            },
                        ),
                        RKeyValue(
                            {
                                "Transaction Number:": f"{res.transaction.transaction_number}",
                            }
                        ),
                        RKeyValue(
                            {
                                "Started Date:": f"{format_reciept_date(res.card.started_date)}",
                            }
                        ),
                        RKeyValue(
                            {
                                "Expiry Date:": f"{format_reciept_date(res.card.expiration_date)}",
                            }
                        ),
                    ],
                ),
                RColumn(
                    [
                        RQRCode(f"{res.id}"),
                        RColumn(
                            [
                                RParagraph(
                                    text=f"{res.sales_number}",
                                    font_size=15,
                                    alignment=TA_LEFT,
                                ),
                            ],
                            p_left=50,
                        ),
                    ],
                    p_top=10,
                ),
            ],
        ),
        RRow(
            [
                RColumn(
                    [
                        RParagraph(
                            "Terms and Conditions:", alignment=TA_LEFT, font_size=10
                        ),
                        RParagraph(
                            f"{res.card.terms_conditions}",
                            alignment=TA_LEFT,
                        ),
                    ],
                    col_width=210,
                ),
            ],
            padding_top=10,
            colwidth=210,
            alignment=Alignment.LEFT,
        ),
        RRow(
            [
                RParagraph(
                    f"Purchased on: {format_reciept_date(res.created_at)}",
                    alignment=TA_LEFT,
                ),
                RParagraph("Powered by: Qixly Card", alignment=TA_CENTER),
            ],
            padding_top=40,
            colwidth=100,
        ),
    ]

    pdfmetrics.registerFont(
        TTFont(get_font_name(), "resources/fonts/Lucida Console Regular.ttf")
    )

    story = [each.get_flowable() for each in data]
    buffer = BytesIO()
    page_size = (15 * inch, 8 * inch)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(page_size),
        rightMargin=40,
        leftMargin=40,
        topMargin=10,
        bottomMargin=10,
    )

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)
    template = PageTemplate("background", [frame], onPage=add_background)

    doc.addPageTemplates([template])
    doc.build(story)
    buffer.seek(0)

    if not file_name:
        file_name = f"{res.user.name}_Ticket_platform_card_receipt.pdf"
    elif ".pdf" not in file_name:
        file_name += ".pdf"

    response = Response(content=buffer.read(), media_type="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename={res.user.name}"

    return response
