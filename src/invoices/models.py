import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Feedback(TimestampMixin):
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    serial_number = models.CharField(
        max_length=50,
        unique=True
    )

    name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    address = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    rating = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('poor', 'Poor'),
        ],
        verbose_name=_('Rating')
    )

    feedback_text = models.TextField(
        verbose_name=_('Feedback')
    )

    attachment = models.FileField(
        upload_to='feedback_attachments/',
        blank=True,
        null=True,
        verbose_name=_('Attachment')
    )

    anonymous = models.BooleanField(
        default=False,
        verbose_name=_('Anonymous')
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('solved', 'Solved'),
            ('closed', 'Closed'),
        ],
        default='pending',
        verbose_name=_('Status')
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks'
    )

    def __str__(self):
        if self.anonymous:
            return f"Anonymous Feedback {self.serial_number}"
        return f"Feedback {self.serial_number} - {self.name or 'Unknown'}"

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'
        ordering = ['-created_at']