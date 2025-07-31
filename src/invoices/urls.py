from django.urls import path
from . import views
from .views import custom_captcha_refresh

app_name = 'invoices'

urlpatterns = [
    path('create-feedback/', views.FeedbackCreateView.as_view(), name='create_feedback'),
    path('create-feedback/<uuid:user_id>/', views.FeedbackCreateView.as_view(), name='create_feedback_with_user'),
    path('view-feedbacks/', views.FeedbackListView.as_view(), name='view_feedbacks'),
    path('manage-feedbacks/', views.ManageFeedbacksView.as_view(), name='manage_feedbacks'),
    path('captcha/refresh/', custom_captcha_refresh, name='captcha-refresh'),
    path('feedback/<uuid:feedback_uuid>/', views.FeedbackDetailView.as_view(), name='feedback_detail'),
    path('feedback/<uuid:feedback_uuid>/download/', views.download_feedback_pdf, name='download_feedback'),
    path('feedback/<uuid:feedback_uuid>/update-status/', views.update_status, name='update_status'),
    path('feedback/<uuid:feedback_uuid>/delete/', views.DeleteFeedbackView.as_view(), name='delete_feedback'),
    path('feedback/<uuid:feedback_uuid>/claim/', views.ClaimFeedbackView.as_view(), name='claim_feedback'),
    path('download-feedbacks/', views.FeedbackDownloadView.as_view(), name='download_feedbacks'),
]