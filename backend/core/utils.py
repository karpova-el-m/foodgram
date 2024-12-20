import os
import io

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


class ShoppingCartPDFGenerator:
    def __init__(self, user, ingredients_summary):
        self.user = user
        self.ingredients_summary = ingredients_summary

    def generate(self):
        """Генерация PDF-файла со списком покупок."""
        FONT_PATH = os.path.join(
            settings.BASE_DIR,
            'fonts',
            'Stamps.ttf'
        )
        buffer = io.BytesIO()
        pdfmetrics.registerFont(TTFont('Stamps', FONT_PATH))
        pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
        pdf_canvas.setFont('Stamps', 12)
        width, height = A4
        pdf_canvas.drawString(
            50, height - 50,
            f'Список покупок для {self.user.username}'
        )
        y_position = height - 100
        for ingredient in self.ingredients_summary:
            line = (
                f'{ingredient["ingredient__name"]} - '
                f'{ingredient["total_amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}'
            )
            pdf_canvas.drawString(50, y_position, line)
            y_position -= 20
            if y_position < 50:
                pdf_canvas.showPage()
                pdf_canvas.setFont('Stamps', 12)
                y_position = height - 50
        pdf_canvas.save()
        buffer.seek(0)
        return buffer.getvalue()
