from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse, JsonResponse
from users.views import get_system_logo
from django.views.generic import ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import datetime
from django.db.models import Q
from django.contrib import messages
from .models import Invoice
from .forms import InvoiceForm
from tenants.models import Tenant
from users.models import UserType
from django.conf import settings
from django.views.decorators.http import require_POST
from users.views import get_system_logo
import io
from django.urls import reverse_lazy
# Create your views here.

def get_invoice_serial_number():
    # Generate a unique serial number for the invoice
    # This is a placeholder implementation. You can customize it as needed.
    import random
    return ''.join(random.choices(datetime.now().strftime("%Y%m%d") + str(random.randint(1000, 9999)), k=10))


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
            tenant = get_object_or_404(Tenant, uuid=tenant_uuid, user=request.user)
            form = InvoiceForm(initial={'tenant': tenant, 'logo': logo})
        else:
            form = InvoiceForm(user=request.user)
        return render(request, self.template_name, {'form': form, 'logo': logo})

    def post(self, request, *args, **kwargs):
        form = InvoiceForm(request.POST)
        logo = get_system_logo()
        if form.is_valid():
            # Generate a unique serial number for the invoice
            serial_number = get_invoice_serial_number()
            invoice = form.save(commit=False)
            invoice.tenant = form.cleaned_data['tenant']
            invoice.serial_number = serial_number
            invoice.save()
            messages.success(request, "इनभ्वाइस सफलतापूर्वक पेश गरियो!")
            return redirect('invoices:view_invoices')
        messages.error(request, form.errors)
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
    

def download_invoice_pdf(request, invoice_uuid):
    invoice = get_object_or_404(
        Invoice.objects.select_related('tenant'),
        uuid=invoice_uuid
    )

    generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logo = get_system_logo()

    html_string = render_to_string('invoices/invoice_pdf.html', {'invoice': invoice, 'logo': logo, 'generated_date': generated_date})
    html = HTML(string=html_string, base_url=request.build_absolute_uri())

    pdf_file = io.BytesIO()
    html.write_pdf(target=pdf_file)

    pdf_file.seek(0)
    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{invoice.serial_number}.pdf"'
    return response

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
