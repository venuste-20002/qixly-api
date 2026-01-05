from enum import Enum

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, Table

font_size = 9


def get_font_name(weight="Regular"):
    return "Helvetica-Bold" if weight == "Bold" else "lucida"


class RNode:
    def get_flowable(self):
        raise NotImplementedError


class RImage(RNode):
    def __init__(self, filename, width=100, height=100):
        self.filename = filename
        self.width = width
        self.height = height

    def get_flowable(self):
        return Image(self.filename, self.width, self.height, hAlign="CENTER")


class RSeparator(RNode):
    def __init__(self, character="-", count=35, alignment=TA_LEFT):
        self.character = character
        self.count = count
        self.alignment = alignment

    def get_flowable(self):
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            name="Normal",
            parent=styles["Normal"],
            fontName=get_font_name(),
            alignment=self.alignment,
            leftIndent=6,
            leading=8,
            spaceAfter=0,
            spaceBefore=0,
        )
        return Paragraph(f"{self.character * self.count}", style=style)


class RKeyValue(RNode):
    def __init__(self, data: dict, font_size=13):
        self.data = data
        self.font_size = font_size

    def get_flowable(self):
        prepared_data = [[k, v] for k, v in self.data.items()]
        return Table(
            prepared_data,
            rowHeights=[10 * mm] * len(self.data),
            colWidths=[70 * mm, 40 * mm],
            hAlign="LEFT",
            vAlign="TOP",
            spaceBefore=0,
            spaceAfter=0,
            style=[
                ("FONT", (0, 0), (-1, -1), get_font_name(), self.font_size),
                ("FONT", (0, -1), (0, -1), get_font_name("Bold"), self.font_size),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ],
        )


class RColumn(RNode):
    def __init__(self, data: list[RNode], p_top=0, p_bottom=0, col_width=90, p_left=0):
        self.data = data
        self.p_top = p_top
        self.p_bottom = p_bottom
        self.p_left = p_left
        self.col_width = col_width

    def get_flowable(self):
        prepared_data = [[node.get_flowable()] for node in self.data]
        return Table(
            prepared_data,
            colWidths=[self.col_width * mm],
            hAlign="RIGHT",
            vAlign="TOP",
            spaceBefore=10,
            spaceAfter=10,
            style=[
                ("FONT", (0, 0), (-1, -1), get_font_name(), font_size),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("TOPPADDING", (0, 0), (-1, -1), self.p_top),
                ("BOTTOMPADDING", (0, 0), (-1, -1), self.p_bottom),
                ("LEFTPADDING", (0, 0), (-1, -1), self.p_left),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ],
        )


class RParagraph(RNode):
    def __init__(
        self,
        text,
        alignment=TA_CENTER,
        font_size=font_size,
        left_indent=0,
    ):
        self.text = text
        self.alignment = alignment
        self.leftIndent = left_indent if alignment == TA_CENTER else 0
        self.font_size = font_size

    def get_flowable(self):
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            name="Normal",
            parent=styles["Normal"],
            fontName=get_font_name(),
            fontSize=self.font_size,
            alignment=self.alignment,
            leftIndent=self.leftIndent,
            spaceBefore=500,
        )
        return Paragraph(f"{self.text}", style=style)


class Alignment(str, Enum):
    CENTER = "CENTER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"

    def __str__(self):
        return self.value


class RRow(RNode):
    def __init__(
        self,
        data: list[RNode],
        padding_top=5,
        colwidth=120,
        alignment: Alignment = Alignment.CENTER,
    ):
        self.data = data
        self.padding_top = padding_top
        self.colwidth = colwidth
        self.alignment = alignment

    def get_flowable(self):
        prepared_data = [node.get_flowable() for node in self.data]
        return Table(
            [prepared_data],
            colWidths=[self.colwidth * mm],
            hAlign="CENTER",
            vAlign="TOP",
            spaceBefore=0,
            spaceAfter=0,
            style=[
                ("FONT", (0, 0), (-1, -1), get_font_name(), font_size),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (0, 0), (-1, -1), f"{self.alignment}"),
                ("TOPPADDING", (0, 0), (-1, -1), self.padding_top),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ],
        )


class RQRCode(RNode):
    def __init__(self, text: str, width=150, height=150):
        self.text = text
        self.width = width
        self.height = height

    def get_flowable(self):
        qr = QrCodeWidget(self.text)
        b = qr.getBounds()

        w = b[2] - b[0]
        h = b[3] - b[1]

        d = Drawing(
            self.width,
            self.height,
            transform=[self.width / w, 0, 0, self.height / h, 0, 0],
        )
        d.add(qr)
        return d
