import uuid
from django.db import models
from django.contrib.auth import get_user_model
from rental_system.mixins import TimestampMixin
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Tenant(TimestampMixin):
    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        unique=True,
        default=uuid.uuid4
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tenants',
        verbose_name=_('user'),
    )

    photo = models.ImageField(
        _('photo'),
        upload_to='tenant_photos/',
        blank=True,
        null=True
    )

    name = models.CharField(
        _('name'),
        max_length=100,
    )

    address = models.CharField(
        _('address'),
        max_length=100,
    )

    mobile = models.CharField(
        _('mobile'),
        max_length=15,
    )

    email = models.EmailField(
        _('email address'),
        unique=True,
    )

    profession = models.CharField(
        _('profession'),
        max_length=100,
        blank=True,
    )

    house_name = models.CharField(
        _('house name'),
        max_length=100,
        blank=True,
    )

    flat_number = models.CharField(
        _('flat number'),
        max_length=10,
    )

    room_number = models.CharField(
        _('room number'),
        max_length=10,
    )

    rent_amount = models.DecimalField(
        _('rent amount'),
        max_digits=10,
        decimal_places=2,
    )

    rent_start_date = models.CharField(
        _('rent start date'),
        max_length=10,
        help_text=_('Format: YYYY-MM-DD'),
        blank=True,
        null=True,
    )

    pan_or_vat_number = models.CharField(
        _('PAN or VAT Number'),
        max_length=50,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name