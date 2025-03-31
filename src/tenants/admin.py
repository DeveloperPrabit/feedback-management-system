from django.contrib import admin
from .models import Tenant

# Register your models here.

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "mobile",)
    search_fields = ("name", "email", "mobile")
    ordering = ("-created_at",)
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'address',
                'mobile',
                'email',
                'profession',
                'house_name',
                'flat_number',
                'room_number',
                'rent_amount',
                'rent_start_date',
                'photo'
            )
        }),
    )

