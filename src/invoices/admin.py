from django.contrib import admin
from .models import Invoice
# Register your models here.


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    list_per_page = 20

    list_filter = ('status',)

    fieldsets = (
        (None, {
            'fields': (
                'serial_number',
                'rent_month',
                'date',
                'tenant',
                'house_number',
                'flat_number',
                'room_no',
                'building_name',
                'rent_amount',
                'parking_fee',
                'electricity_fee',
                'security_fee',
                'discount',
                'total_amount',
                'tax',
                'grand_total',
                'bank_name',
                'account_number',
                'account_name',
                'owner_signature',
                'tenant_signature',
                'status'
            )
        }),
    )