from django.shortcuts import render, redirect, get_object_or_404
from .models import Tenant
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.generic import ListView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from users.models import UserType
from .forms import TenantForm
from users.views import get_system_logo


# Create your views here.

class TenantListView(LoginRequiredMixin, ListView):
    model = Tenant
    context_object_name = 'tenants'
    paginate_by = 5
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user.user_type == UserType.ADMIN:
            search_query = self.request.GET.get('search', '')
            if search_query:
                return Tenant.objects.filter(
                    Q(name__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(mobile__icontains=search_query)
                ).order_by('-created_at')
            else:
                return Tenant.objects.all().order_by('-created_at')
        else:
            search_query = self.request.GET.get('search', '')
            if search_query:
                return Tenant.objects.filter(
                    Q(name__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(mobile__icontains=search_query),
                    user=self.request.user
                ).order_by('-created_at')
            else:
                return Tenant.objects.filter(user=self.request.user).order_by('-created_at')
        
    def get_template_names(self):
        if self.request.user.user_type == UserType.ADMIN:
            return ['tenants/tenant_list.html']
        else:
            return ['tenants/user_tenant_list.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        return context
        

class ManageTenantView(LoginRequiredMixin, ListView):
    model = Tenant
    template_name = 'tenants/manage_tenant.html'
    context_object_name = 'tenants'
    paginate_by = 5

    def get_queryset(self):
        if self.request.user.user_type == UserType.ADMIN:
            search_query = self.request.GET.get('search', '')
            if search_query:
                return Tenant.objects.filter(
                    Q(name__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(mobile__icontains=search_query)
                ).order_by('-created_at')
            else:
                return Tenant.objects.all().order_by('-created_at')
        else:
            search_query = self.request.GET.get('search', '')
            if search_query:
                return Tenant.objects.filter(
                    Q(name__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(mobile__icontains=search_query),
                    user=self.request.user
                ).order_by('-created_at')
            else:
                return Tenant.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logo"] = get_system_logo() 
        return context
    
    


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
        if request.user.user_type == UserType.ADMIN:
            return render(request, 'tenants/add_tenant.html', {'form': form})
        else:
            return render(request, 'tenants/add_user_tanant.html', {'form': form})
    
    def post(self, request):
        form = TenantForm(request.POST, request.FILES)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.user = request.user
            tenant.save()
            messages.success(request, "Tenant added successfully")
            if request.user.user_type != UserType.ADMIN:
                return redirect('users:dashboard')
            return redirect('tenants:manage_tenants')
        else:
            if request.user.user_type == UserType.ADMIN:
                messages.error(request, "Failed to add tenant. Please check the form.")
                messages.error(request, form.errors)
                return render(request, 'tenants/add_tenant.html', {'form': form})
            else:
                messages.error(request, "Failed to add tenant. Please check the form.")
                messages.error(request, form.errors)
                return render(request, 'tenants/add_user_tanant.html', {'form': form})
    
@method_decorator(login_required, name='dispatch')
class TenantUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tenant
    form_class = TenantForm
    template_name = 'tenants/update_tenant.html'
    success_url = reverse_lazy('tenants:manage_tenants')
    context_object_name = 'tenant'
    pk_url_kwarg = 'tenant_uuid'

    def test_func(self):
        tenant = self.get_object()
        if self.request.user.user_type == UserType.ADMIN:
            return True
        return False
    
    def form_valid(self, form):
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class TenantDetailsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Tenant
    template_name = 'tenants/tenant_details.html'
    context_object_name = 'tenant'
    pk_url_kwarg = 'tenant_uuid'

    def test_func(self):
        tenant = self.get_object()
        if self.request.user.user_type == UserType.ADMIN:
            return True
        return tenant.user == self.request.user


    
    def get_template_names(self):
        if self.request.user.user_type == UserType.ADMIN:
            return ['tenants/tenant_details.html']
        else:
            return ['tenants/user_tenant_details.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.object
        context['logo'] = get_system_logo()
        return context
    







