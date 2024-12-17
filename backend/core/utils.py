import os

from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def generate_shopping_cart_pdf(user, ingredients_summary):
    """Генерация PDF-файла со списком покупок."""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_cart.pdf"'
    )
    FONT_PATH = os.path.join(
        settings.BASE_DIR,
        'fonts',
        'Stamps.ttf'
    )
    pdfmetrics.registerFont(TTFont('Stamps', FONT_PATH))
    pdf_canvas = canvas.Canvas(response, pagesize=A4)
    pdf_canvas.setFont('Stamps', 12)
    width, height = A4
    pdf_canvas.drawString(
        50, height - 50,
        f'Список покупок для {user.username}'
    )
    y_position = height - 100
    for ingredient in ingredients_summary:
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
    return response
