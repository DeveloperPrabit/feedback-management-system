from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'Rental System Admin'
admin.site.site_title = 'Rental System Admin'
admin.site.index_title = 'Welcome to Rental System Admin'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/in/', admin.site.urls),
    path('', include('users.urls', namespace='users')),
    path('', include('tenants.urls', namespace='tenants')),
    path('', include('invoices.urls', namespace='invoices')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)