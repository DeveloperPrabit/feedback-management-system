import uuid
from django.db import models
from rental_system.mixins import TimestampMixin
from django.utils.translation import gettext_lazy as _
from tenants.models import Tenant
    
class Invoice(TimestampMixin):
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

    rent_month = models.CharField(
        max_length=20
    )

    date = models.DateField()

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_('tenant')
    )

    house_number = models.CharField(
        max_length=20
    )

    flat_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True
    )

    room_no = models.CharField(
        max_length=20
    )

    building_name = models.CharField(
        max_length=100
    )

    rent_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )

    parking_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )

    electricity_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )

    security_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )

    discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )

    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )

    tax = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )

    grand_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )

    bank_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )

    account_number = models.CharField(
        max_length=50, 
        blank=True, 
        null=True
    )

    account_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )

    owner_signature = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )

    tenant_signature = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('paid', _('Paid')),
            ('unpaid', _('Unpaid')),
            ('overdue', _('Overdue')),
        ],
        default='unpaid',
    )

    def __str__(self):
        return f"Invoice {self.serial_number} - {self.tenant}"
    

    class Meta:
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')
        ordering = ['-date']
    