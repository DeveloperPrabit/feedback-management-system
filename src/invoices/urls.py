from django.urls import path
from . import views

app_name = 'invoices'
urlpatterns = [
    path('view-invoices/', views.InvoiceListView.as_view(), name='view_invoices'),
    path('create-invoice/', views.InvoiceCreateView.as_view(), name='create_invoice'),
    path('invoice/<uuid:invoice_uuid>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('manage-invoices/', views.ManageInvoicesView.as_view(), name='manage_invoices'),
    path('delete-invoice/<uuid:invoice_uuid>/', views.DeleteInvoiceView.as_view(), name='delete_invoice'),
    path('invoice/<uuid:invoice_uuid>/download/', views.download_invoice_pdf, name='download_invoice')
]
