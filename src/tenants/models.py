import uuid
from django.db import models
from rental_system.mixins import TimestampMixin
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Tenant(TimestampMixin):
    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        unique=True,
        default=uuid.uuid4
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
        default='Unknown',
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

    rent_start_date = models.DateField(
        _('rent start date'),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name
    