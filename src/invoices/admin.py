from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'serial_number', 'created_at', 'status')
    list_per_page = 20
    list_filter = ('status', 'rating', 'anonymous')
    search_fields = ('name', 'email', 'mobile', 'address', 'feedback_text', 'serial_number')

    fieldsets = (
        (None, {
            'fields': (
                'serial_number', 'created_at', 'name', 'address',
                'mobile', 'email', 'rating', 'feedback_text', 'attachment',
                'anonymous', 'status'
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.user_type != 'ADMIN':
            return qs.filter(created_by=request.user)
        return qs