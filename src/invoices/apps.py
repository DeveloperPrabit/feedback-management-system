from django.apps import AppConfig
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from django.conf import settings

class InvoicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoices'

    def ready(self):
        font_path = os.path.join(settings.STATIC_ROOT, 'fonts', 'NotoSansDevanagari-Regular.ttf')
        if os.path.isfile(font_path):
            pdfmetrics.registerFont(TTFont('NotoSansDevanagari', font_path))
        else:
            print(f"Font file not found at: {font_path}")