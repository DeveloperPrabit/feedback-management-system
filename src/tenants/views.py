from django.shortcuts import render, redirect, get_object_or_404
from .models import Tenant
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.generic import ListView, UpdateView, DetailView
from users.models import UserType
from .forms import TenantForm


# Create your views here.

@method_decorator(login_required, name='dispatch')
class TenantListView(ListView):
    model = Tenant
    template_name = 'tenants/tenant_list.html'
    context_object_name = 'tenants'
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        return Tenant.objects.all().order_by('-created_at')

@method_decorator(login_required, name='dispatch')
class ManageTenantView(TenantListView):
    template_name = 'tenants/manage_tenant.html'

@method_decorator(login_required, name='dispatch')
class DeleteTenantView(View):

    def post(self, request, tenant_uuid):
        tenant = get_object_or_404(Tenant, uuid=tenant_uuid)
        if request.user.user_type != UserType.ADMIN:
            messages.error(request, "You do not have permission to delete this tenant.")
            return redirect('tenants:manage_tenants')
        tenant.delete()
        messages.success(request, "Tenant deleted successfully.")
        return redirect('tenants:manage_tenants')

@method_decorator(login_required, name='dispatch')
class AddTenant(View):

    def get(self, request):
        form = TenantForm()
        return render(request, 'tenants/add_tenant.html', {'form': form})






