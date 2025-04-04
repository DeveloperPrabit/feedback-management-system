from django.urls import path
from . import views

app_name = 'tenants'
urlpatterns = [
    path('view-tenants/', views.TenantListView.as_view(), name='view_tenants'),
    path('manage-tenants/', views.ManageTenantView.as_view(), name='manage_tenants'),
    path('delete-tenant/<uuid:tenant_uuid>/', views.DeleteTenantView.as_view(), name='delete_tenant'),
    path('add-tenant/', views.AddTenant.as_view(), name='add_tenant'),
    path('edit-tenant/<uuid:tenant_uuid>/', views.TenantUpdateView.as_view(), name='edit_tenant'),
    path('tenant/<uuid:tenant_uuid>/', views.TenantDetailsView.as_view(), name='tenant_details'),
]
