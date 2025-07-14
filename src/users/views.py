import random
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db.models import Q
from django.db import transaction
import requests
from .forms import (
    UserLoginForm,
    CustomPasswordChangeForm,
    EditUserForm
)
from .models import UserType, PasswordResetOTP, SystemLogo, Contact
from tenants.models import Tenant
from invoices.models import Invoice
from .utils import send_otp_email

# Create your views here.

User = get_user_model()

def get_system_logo():
    try:
        logo = SystemLogo.objects.latest('-created_at')
    except SystemLogo.DoesNotExist:
        logo = None
    return logo

class UserRegisterView(View):
    template_name = 'users/register.html'
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        logo = get_system_logo()

        context = {
            'logo': logo,
        }
        # Check if the user is already authenticated
        return render(request, self.template_name, context)
    
    def post(self, request):
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        full_address = request.POST.get('full_address')
        mobile = request.POST.get('mobile')
        terms = request.POST.get('terms')

        errors = []

        # Validate required fields
        if not all([full_name, full_address, email, mobile, password, terms]):
            errors.append("All fields are required.")

        if not mobile.isdigit() or len(mobile) != 10:
            errors.append("Enter a valid 10-digit mobile number.")


        # Validate unique email
        if User.objects.filter(email=email).exists():
            errors.append("This email is already registered.")

        # Validate password length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if not terms:
            messages.error(request, "You must accept the terms and conditions.")

        if errors:
            for error in errors:
                messages.error(request, error)
            # Send back the filled data
            return render(request, self.template_name, {
                "email": email,
                "full_name": full_name,
                "full_address": full_address,
                "mobile": mobile,
            })
        
        # Verify Google reCAPTCHA
        recaptcha_response = request.POST.get("g-recaptcha-response")
        recaptcha_secret = "6LfswtgZAAAAABX9gbLqe-d97qE2g1JP8oUYritJ"  # Replace with actual reCAPTCHA secret key
        recaptcha_verify_url = "https://www.google.com/recaptcha/api/siteverify"
        recaptcha_data = {"secret": recaptcha_secret, "response": recaptcha_response}
        recaptcha_result = requests.post(recaptcha_verify_url, data=recaptcha_data).json()

        # if not recaptcha_result.get("success"):
        #     messages.error(request, "Invalid reCAPTCHA. Please try again.")
        #     return redirect("users:register")
        
        # Create user
        user = User.objects.create(
            email=email,
            full_name=full_name,
            full_address=full_address,
            mobile=mobile,
        )
        user.set_password(password)
        user.save()

        messages.success(request, "Registration successful. You can now log in.")
        return redirect("users:login")


class UserLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        form = UserLoginForm()
        logo = get_system_logo()
        return render(request, 'users/login.html', {'form': form, 'logo': logo})
    
    def post(self, request):
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("users:dashboard")
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid form submission.")
        
        logo = get_system_logo()
        return render(request, 'users/login.html', {'form': form, 'logo': logo})

class UserLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("users:login")

    def post(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("users:login")

@method_decorator(login_required, name='dispatch')
class PasswordChangeView(View):
    def get(self, request):
        form = CustomPasswordChangeForm(user=request.user)
        if request.user.user_type == UserType.ADMIN:
            return render(request, 'users/admin_password_change.html', {'form': form})
        return render(request, 'users/change_password.html', {'form': form})
    
    def post(self, request):
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password changed successfully.")
            return redirect("users:login")
        else:
            messages.error(request, "Invalid form submission.")
        if request.user.user_type == UserType.ADMIN:
            return render(request, 'users/admin_password_change.html', {'form': form})
        # If the user is not an admin, render the normal password change page
        return render(request, 'users/change_password.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        if request.user.user_type == UserType.ADMIN:
            users = User.objects.all().count()
            tenants = Tenant.objects.all().count()
            invoices = Invoice.objects.all().count()
            paid_invoices = Invoice.objects.filter(status__iexact='paid').count()
            unpaid_invoices = Invoice.objects.filter(status__iexact='unpaid').count()

            context = {
                'users': users,
                'tenants': tenants,
                'invoices': invoices,
                'paid_invoices': paid_invoices,
                'unpaid_invoices': unpaid_invoices,
                'logo': get_system_logo(),            
            }
            return render(request, 'users/dashboard/admin_index.html', context)
        else:
            context = {
                'tenants': Tenant.objects.filter(user=request.user).count(),
                'invoices': Invoice.objects.filter(tenant__user=request.user).count(),
                'paid_invoices': Invoice.objects.filter(tenant__user=request.user, status__iexact='paid').count(),
                'unpaid_invoices': Invoice.objects.filter(tenant__user=request.user, status__iexact='unpaid').count(),
                'logo': get_system_logo(),
            }
            return render(request, 'users/dashboard/user_index.html', context)
    
    def post(self, request):
        pass

class ViewUsersView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'users/dashboard/view_users.html'
    context_object_name = 'users'
    paginate_by = 5

    def test_func(self):
        return self.request.user.user_type == UserType.ADMIN
    
    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        if search_query:
            return User.objects.filter( 
                Q(email__icontains=search_query) | 
                Q(full_name__icontains=search_query) | 
                Q(mobile__icontains=search_query)
            ).exclude(uuid=self.request.user.uuid)
        return User.objects.exclude(uuid=self.request.user.uuid)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['logo'] = get_system_logo()
        return context
    
    # def get(self, request):
    #     search_query = request.GET.get('search', '')
    #     print(request.user.user_type)
    #     if request.user.user_type == UserType.ADMIN:
    #         if search_query:
    #             users = User.objects.filter( 
    #                 Q(email__icontains=search_query) | 
    #                 Q(full_name__icontains=search_query) | 
    #                 Q(mobile__icontains=search_query)
    #             ).exclude(uuid=request.user.uuid)
    #         else:
    #             users = User.objects.all().exclude(uuid=request.user.uuid)
    #         context = {
    #             'users': users,
    #             'search_query': search_query,
    #         }
    #         return render(request, 'users/dashboard/view_users.html', context)
    #     return render(request, 'users/dashboard/user_index.html')
    
    # def post(self, request):
    #     pass


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'users/profile.html'

    def get(self, request):
        user = request.user
        if request.user.user_type == UserType.ADMIN:
            return render(request, 'users/dashboard/admin_index.html')
        return render(request, self.template_name, {'user': user})
    

@method_decorator(login_required, name='dispatch')
class UpdateProfileView(View):


    def get_template_names(self) -> list[str]:
        if self.request.user.user_type == UserType.ADMIN:
            return ['users/admin_profile_update.html']
        return ['users/update_profile.html']


    def get(self, request):
        user = request.user
        return render(request, self.get_template_names(), {'user': user, 'logo': get_system_logo()})
    

    def post(self, request):
        user = request.user
        profile_picture = request.FILES.get('profile_picture')

        if profile_picture:
            if user.profile_picture:
                default_storage.delete(user.profile_picture.path)
            user.profile_picture = profile_picture
            user.save()
            return redirect("users:dashboard")
        else:
            messages.error(request, "No profile picture uploaded.")
            return render(request, self.get_template_names(), {'user': user, 'logo': get_system_logo()})
    
        

@method_decorator(login_required, name='dispatch')
class UserDeleteView(View):

    def post(self, request, user_uuid):
        user = User.objects.get(uuid=user_uuid)

        if user and request.user.user_type == UserType.ADMIN:
            # Check if the user is not the same as the logged-in user
            if user != request.user:
                user.delete()
        else:
            messages.error(request, "User not found.")

        return redirect("users:manage_users")
    
@method_decorator(login_required, name='dispatch')
class AddUserView(View):
    template_name = 'users/add_user.html'

    def get(self, request):
        if request.user.user_type != UserType.ADMIN:
            messages.error(request, "You do not have permission to access this page.")
            return redirect("users:dashboard")
        return render(request, self.template_name, {"logo": get_system_logo()})
    
    def post(self, request):
        if request.user.user_type != UserType.ADMIN:
            messages.error(request, "You do not have permission to access this page.")
            return redirect("users:dashboard")
        # Get form data
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        full_address = request.POST.get('full_address')
        mobile = request.POST.get('mobile')

        errors = []

        # Validate required fields
        if not all([full_name, full_address, email, mobile, password]):
            errors.append("All fields are required.")

        if not mobile.isdigit() or len(mobile) != 10:
            errors.append("Enter a valid 10-digit mobile number.")


        # Validate unique email
        if User.objects.filter(email=email).exists():
            errors.append("This email is already registered.")

        # Validate password length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if errors:
            for error in errors:
                messages.error(request, error)
            # Send back the filled data
            return render(request, self.template_name, {
                "email": email,
                "full_name": full_name,
                "full_address": full_address,
                "mobile": mobile,
            })
        
        # Create user
        user = User.objects.create(
            email=email,
            full_name=full_name,
            full_address=full_address,
            mobile=mobile,
        )
        user.set_password(password)
        user.save()

        messages.success(request, "User added successfully.")
        return redirect("users:manage_users")

class ManageUsersView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    context_object_name = 'users'
    paginate_by = 5
    template_name = 'users/dashboard/manage_users.html'

    def test_func(self):
        return self.request.user.user_type == UserType.ADMIN
    
    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        if search_query:
            return User.objects.filter( 
                Q(email__icontains=search_query) | 
                Q(full_name__icontains=search_query) | 
                Q(mobile__icontains=search_query)
            ).exclude(uuid=self.request.user.uuid)
        return User.objects.exclude(uuid=self.request.user.uuid)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['logo'] = get_system_logo()
        return context

    # def get(self, request):
    #     search_query = request.GET.get('search', '')
    #     if request.user.user_type != UserType.ADMIN:
    #         messages.error(request, "You do not have permission to access this page.")
    #         return redirect("users:dashboard")
        
    #     if search_query:
    #         users = User.objects.filter( 
    #             Q(email__icontains=search_query) | 
    #             Q(full_name__icontains=search_query) | 
    #             Q(mobile__icontains=search_query)
    #         ).exclude(uuid=request.user.uuid)
    #     else:
    #         users = User.objects.all().exclude(uuid=request.user.uuid)
    #     return render(request, self.template_name, {'users': users})
    

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    template_name = 'users/update_user.html'
    form_class = EditUserForm
    success_url = reverse_lazy('users:manage_users')
    context_object_name = 'user'
    pk_url_kwarg = 'user_uuid'

    def test_func(self):
        user = self.get_object()
        if self.request.user.user_type == UserType.ADMIN:
            return True
        return False
    
    def form_valid(self, form):
        password = form.cleaned_data.get('password')
        if password:
            self.object.set_password(password)  # Set hashed password
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        return context


class ForgotPasswordView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        logo = get_system_logo()
        context = {
            'logo': logo,
        }
        return render(request, 'users/forgot_password.html', context)

    def post(self, request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "User with this email does not exist.")
            return redirect("users:forgot_password")
        
        # Generate OTP
        otp = f"{random.randint(100000, 999999)}"
        otp_record = PasswordResetOTP.objects.filter(user=user).order_by('-created_at').first()
        if otp_record:
            otp_record.otp = otp
            otp_record.save(update_fields=['otp', 'created_at', 'updated_at'])
        else:
            PasswordResetOTP.objects.create(user=user, otp=otp)

        # Send OTP to user's email (implement your email sending logic here)
        send_otp_email(user.email, otp)
        messages.success(request, f"An OTP has been sent to {user.email}.")
        request.session['request_user_id'] = str(user.uuid)
        return redirect('users:verify_otp')
    

class VerifyOTPView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        system_logo = get_system_logo()
        context = {
            'logo': system_logo,
        }
        
        return render(request, 'users/verify_otp.html', context)

    def post(self, request):
        otp = request.POST.get('otp')
        user_uuid = request.session.get('request_user_id')

        if not user_uuid:
            messages.error(request, "Session expired. Please request a new OTP.")
            return redirect("users:forgot_password")
        
        user = User.objects.get(uuid=user_uuid)
        otp_record = PasswordResetOTP.objects.filter(user=user).order_by('-created_at').first()

        if otp_record and otp_record.is_valid() and otp_record.otp == otp:
            # OTP is valid
            request.session['otp_verified'] = True
            return redirect('users:reset_password')
        else:
            messages.error(request, "Invalid or expired OTP.")
            return redirect("users:verify_otp")
        

class ResetPasswordView(View):
    def get(self, request):
        if not request.session.get('otp_verified'):
            messages.error(request, "Please verify your OTP first.")
            return redirect("users:forgot_password")
        
        system_logo = get_system_logo()
        context = {
            'logo': system_logo,
        }
        return render(request, 'users/reset_password.html', context)
    
    @transaction.atomic
    def post(self, request):
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("users:reset_password")
        
        user_uuid = request.session.get('request_user_id')

        if not user_uuid:
            messages.error(request, "Session expired. Please request a new OTP.")
            return redirect("users:forgot_password")
        
        user = User.objects.get(uuid=user_uuid)
        user.set_password(password)
        user.save()

        request.session.flush()
        messages.success(request, "Password reset successfully. You can now log in.")
        return redirect('users:login')
    

@method_decorator(login_required, name='dispatch')
class ContactView(View):
    def get(self, request):
        logo = get_system_logo()
        contact = Contact.objects.first()
        context = {
            'logo': logo,
            'contact': contact,
        }
        return render(request, 'users/contact.html', context)