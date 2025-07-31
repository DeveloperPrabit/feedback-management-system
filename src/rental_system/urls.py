# rental_system/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from invoices.views import custom_404

admin.site.site_header = 'FeedBox | Digital Feedback Box | Nepal Admin'
admin.site.site_title = 'FeedBox | Digital Feedback Box | Nepal Admin'
admin.site.index_title = 'Welcome to FeedBox | Digital Feedback Box | Nepal Admin'

handler404 = 'invoices.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/in/', admin.site.urls),
    path('', include('users.urls', namespace='users')),
    path('', include('tenants.urls', namespace='tenants')),
    path('', include('invoices.urls', namespace='invoices')),
    path('captcha/', include('captcha.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)