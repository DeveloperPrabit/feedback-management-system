from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from weasyprint import HTML
from django.db.models import Q
from django.contrib import messages
from .models import Invoice
from .forms import InvoiceForm
from tenants.models import Tenant
from users.models import UserType

# Create your views here.

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
    


@method_decorator(login_required, name='dispatch')
class InvoiceCreateView(View):
    template_name = 'invoices/create_invoice.html'

    def get(self, request, *args, **kwargs):
        tenant_uuid = request.GET.get('tenant_uuid')
        if tenant_uuid:
            tenant = get_object_or_404(Tenant, uuid=tenant_uuid, user=request.user)
            form = InvoiceForm(initial={'tenant': tenant})
        else:
            form = InvoiceForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.tenant = form.cleaned_data['tenant']
            invoice.save()
            messages.success(request, "इनभ्वाइस सफलतापूर्वक पेश गरियो!")
            return redirect('invoices:view_invoices')
        messages.error(request, form.errors)
        return render(request, self.template_name, {'form': form})


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
    invoice = get_object_or_404(Invoice, uuid=invoice_uuid)

    html_string = render_to_string('invoices/invoice_pdf.html', {'invoice': invoice})

    pdf = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.serial_number}.pdf"'
    return response