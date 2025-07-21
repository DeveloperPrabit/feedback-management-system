from django.apps import AppConfig
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class InvoicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoices'

    def ready(self):
        font_path = os.path.normpath(os.path.join(settings.STATIC_ROOT, 'fonts', 'NotoSansDevanagari-Regular.ttf'))
        logger.debug(f"Attempting to register font at: {font_path}")
        if os.path.isfile(font_path):
            try:
                pdfmetrics.registerFont(TTFont('NotoSansDevanagari', font_path))
                logger.debug("Font 'NotoSansDevanagari' registered successfully")
            except Exception as e:
                logger.error(f"Failed to register font: {str(e)}")
        else:
            logger.error(f"Font file not found at: {font_path}")