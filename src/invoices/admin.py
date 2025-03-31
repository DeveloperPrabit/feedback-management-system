from django.contrib import admin
from .models import Invoice, RentInvoice
# Register your models here.

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    search_fields = (
        'invoice_number',
        'tenant__name',
        'tenant__email',
    )
    list_filter = ('status', 'tenant')
    ordering = ('-date_issued',)
    date_hierarchy = 'date_issued'
    list_per_page = 20
    list_select_related = ('tenant',)

    fieldsets = (
        (None, {
            'fields': ('invoice_number', 'tenant', 'date_due', 'total_amount', 'status')
        }),
    )


@admin.register(RentInvoice)
class RentInvoiceAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': (
                'serial_number',
                'rent_month',
                'date',
                'tenant_name',
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
            )
        }),
    )