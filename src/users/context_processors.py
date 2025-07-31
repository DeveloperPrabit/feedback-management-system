from invoices.models import Feedback
from django.db.models import Q

def feedback_context(request):
    if request.user.is_authenticated and request.user.user_type != 'admin':
        feedback_queryset = Feedback.objects.filter(
            Q(email=request.user.email) |
            Q(mobile=request.user.mobile) |
            Q(created_by=request.user) |
            Q(uuid__in=request.user.feedbacks.values_list('uuid', flat=True))
        ).distinct()
        return {
            'reviewed_feedbacks': feedback_queryset.filter(status__in=['solved', 'closed']).count()
        }
    return {'reviewed_feedbacks': 0}

from django.conf import settings

def site_settings(request):
    return {
        'SITE_URL': settings.SITE_URL,
        'DEBUG': settings.DEBUG,
    }