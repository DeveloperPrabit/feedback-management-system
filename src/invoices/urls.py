from django.urls import path
from . import views

app_name = 'invoices'
urlpatterns = [
    path('view-feedbacks/', views.FeedbackListView.as_view(), name='view_feedbacks'),
    path('create-feedback/', views.FeedbackCreateView.as_view(), name='create_feedback'),
    path('feedback/<uuid:feedback_uuid>/', views.FeedbackDetailView.as_view(), name='feedback_detail'),
    path('manage-feedbacks/', views.ManageFeedbacksView.as_view(), name='manage_feedbacks'),
    path('feedback/<uuid:feedback_uuid>/download/', views.download_feedback_pdf, name='download_feedback'),
    path('update-status/<uuid:feedback_uuid>/', views.update_status, name='update_status'),
]