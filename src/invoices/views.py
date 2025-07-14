from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse, JsonResponse
from users.views import get_system_logo
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from datetime import datetime
from django.db.models import Q
from django.contrib import messages
from .models import Invoice
from .forms import InvoiceForm
from tenants.models import Tenant
from users.models import UserType
from django.conf import settings
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
import io
import os
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
import random
import logging

logger = logging.getLogger(__name__)

def get_invoice_serial_number():
    return ''.join(random.choices(datetime.now().strftime("%Y%m%d") + str(random.randint(1000, 9999)), k=10))

@login_required
def get_tenant_details(request):
    tenant_id = request.GET.get('tenant_id')
    if not tenant_id:
        return JsonResponse({'error': 'Tenant ID is required'}, status=400)
    
    try:
        tenant = Tenant.objects.get(id=tenant_id, user=request.user)
        data = {
            'house_name': tenant.house_name,
            'flat_number': tenant.flat_number,
            'room_number': tenant.room_number,
            'rent_amount': str(tenant.rent_amount),
            'rent_start_date': tenant.rent_start_date,
            'pan_or_vat_number': tenant.pan_or_vat_number or '',
        }
        return JsonResponse(data)
    except Tenant.DoesNotExist:
        return JsonResponse({'error': 'Tenant not found'}, status=404)

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    context_object_name = 'invoices'
    paginate_by = 5
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        status = self.request.GET.get('status', '')

        if self.request.user.user_type == UserType.ADMIN:
            queryset = Invoice.objects.all()
        else:
            queryset = Invoice.objects.filter(
                tenant__user=self.request.user
            )

        if search:
            queryset = queryset.filter(
                Q(tenant__name__icontains=search) |
                Q(tenant__email__icontains=search) |
                Q(tenant__mobile__icontains=search) |
                Q(house_number__icontains=search) |
                Q(flat_number__icontains=search) |
                Q(room_no__icontains=search) |
                Q(building_name__icontains=search) |
                Q(serial_number__icontains=search)
            ).distinct()

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')
    
    def get_template_names(self):
        if self.request.user.user_type == UserType.ADMIN:
            return ['invoices/invoice_list.html']
        return ['invoices/user_invoice_list.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        return context

class ManageInvoicesView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices/manage_invoices.html'
    context_object_name = 'invoices'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        status = self.request.GET.get('status', '')

        if self.request.user.user_type == UserType.ADMIN:
            queryset = Invoice.objects.all()
        else:
            queryset = Invoice.objects.filter(
                tenant__user=self.request.user
            )

        if search:
            queryset = queryset.filter(
                Q(tenant__name__icontains=search) |
                Q(tenant__email__icontains=search) |
                Q(tenant__mobile__icontains=search) |
                Q(house_number__icontains=search) |
                Q(flat_number__icontains=search) |
                Q(room_no__icontains=search) |
                Q(building_name__icontains=search) |
                Q(serial_number__icontains=search)
            ).distinct()

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at') 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        return context

@method_decorator(login_required, name='dispatch')
class InvoiceCreateView(View):
    template_name = 'invoices/create_invoice.html'

    def get(self, request, *args, **kwargs):
        tenant_uuid = request.GET.get('tenant_uuid')
        logo = get_system_logo()

        if tenant_uuid:
            try:
                tenant = Tenant.objects.get(uuid=tenant_uuid, user=request.user)
                initial_data = {
                    'tenant': tenant.id,
                    'house_number': tenant.house_name,
                    'flat_number': tenant.flat_number,
                    'room_no': tenant.room_number,
                    'building_name': tenant.house_name,
                    'pan_or_vat_number': tenant.pan_or_vat_number,
                    'rent_amount': tenant.rent_amount,
                    'date': tenant.rent_start_date,
                }
                form = InvoiceForm(initial=initial_data, user=request.user)
            except Tenant.DoesNotExist:
                messages.error(request, "Tenant not found.")
                form = InvoiceForm(user=request.user)
        else:
            form = InvoiceForm(user=request.user)

        return render(request, self.template_name, {'form': form, 'logo': logo})

    def post(self, request, *args, **kwargs):
        form = InvoiceForm(request.POST, user=request.user)
        logo = get_system_logo()

        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.serial_number = get_invoice_serial_number()
            invoice.save()
            messages.success(request, "इनभ्वाइस सफलतापूर्वक पेश गरियो!")
            return redirect('invoices:view_invoices')

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form, 'logo': logo})

@method_decorator(login_required, name='dispatch')
class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'
    pk_url_kwarg = 'invoice_uuid'

    def get_queryset(self):
        if self.request.user.user_type == UserType.ADMIN:
            return Invoice.objects.all()
        else:
            return Invoice.objects.filter(tenant__user=self.request.user)
        
    def get_template_names(self):
        if self.request.user.user_type == UserType.ADMIN:
            return ['invoices/invoice_detail.html']
        return ['invoices/user_invoice_detail.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.get_object()
        context['logo'] = get_system_logo()
        context['pdf_url'] = self.request.build_absolute_uri(
            reverse_lazy('invoices:download_invoice', kwargs={'invoice_uuid': invoice.uuid})
        )
        return context

@method_decorator(login_required, name='dispatch')
class DeleteInvoiceView(View):
    def post(self, request, invoice_uuid, *args, **kwargs):
        if self.request.user.user_type == UserType.ADMIN:
            invoice = get_object_or_404(Invoice, uuid=invoice_uuid)
            invoice.delete()
            messages.success(request, "इनभ्वाइस सफलतापूर्वक हटाइयो!")
            return redirect('invoices:manage_invoices')
        else:
            invoice = get_object_or_404(Invoice, uuid=invoice_uuid, tenant__user=request.user)
            invoice.delete()
            messages.success(request, "इनभ्वाइस सफलतापूर्वक हटाइयो!")
            return redirect('invoices:view_invoices')

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths for xhtml2pdf.
    Handles Windows paths and skips Base64 data URLs.
    """
    logger.debug(f"Processing URI: {uri}")

    # Skip Base64 data URLs
    if uri.startswith('data:'):
        logger.debug(f"Skipping Base64 data URL: {uri}")
        return uri

    # Normalize URI for Windows
    clean_uri = uri.replace(settings.STATIC_URL, '', 1).lstrip('/').replace('/', os.sep)

    # Try to find the file using Django's static file finder
    path = finders.find(clean_uri)
    if path and os.path.isfile(path):
        logger.debug(f"Resolved static file: {path}")
        return path

    # Fallback to STATIC_ROOT
    path = os.path.join(settings.STATIC_ROOT, clean_uri)
    if os.path.isfile(path):
        logger.debug(f"Resolved static path: {path}")
        return path

    # Handle media URLs
    if uri.startswith(settings.MEDIA_URL):
        clean_uri = uri.replace(settings.MEDIA_URL, '', 1).lstrip('/').replace('/', os.sep)
        path = os.path.join(settings.MEDIA_ROOT, clean_uri)
        if os.path.isfile(path):
            logger.debug(f"Resolved media path: {path}")
            return path

    logger.error(f"File not found: {path}")
    raise Exception(f"File not found: {path}")

@login_required
def download_invoice_pdf(request, invoice_uuid):
    try:
        invoice = get_object_or_404(
            Invoice.objects.select_related('tenant'),
            uuid=invoice_uuid
        )
        generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logo = get_system_logo()
        html_string = render_to_string('invoices/invoice_pdf.html', {
            'invoice': invoice,
            'logo': logo,
            'generated_date': generated_date
        })

        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(
            src=html_string,
            dest=pdf_buffer,
            link_callback=link_callback
        )

        if pisa_status.err:
            logger.error(f"PDF generation error: {pisa_status.err}")
            return HttpResponse(f'Error generating PDF: {pisa_status.err}')

        pdf_buffer.seek(0)
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.serial_number}.pdf"'
        return response

    except Exception as e:
        logger.error(f"Exception in download_invoice_pdf: {str(e)}")
        return HttpResponse(f'Exception occurred: {str(e)}')

@login_required
@require_POST
def update_status(request, invoice_uuid):
    invoice = get_object_or_404(Invoice, uuid=invoice_uuid)
    new_status = request.POST.get('status')
    if new_status in ['paid', 'unpaid', 'overdue']:
        invoice.status = new_status
        invoice.save()
    else:
        messages.error(request, "Invalid status.")
    if request.user.user_type == UserType.ADMIN:
        return redirect('invoices:manage_invoices')
    else:
        return redirect('invoices:view_invoices')