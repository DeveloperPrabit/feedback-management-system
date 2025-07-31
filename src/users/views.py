import random
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db.models import Q, Count
from django.db import transaction
import requests
from .forms import (
    UserLoginForm,
    CustomPasswordChangeForm,
    EditUserForm
)
from .models import UserType, PasswordResetOTP, SystemLogo, Contact
from invoices.models import Feedback
from .utils import send_otp_email

User = get_user_model()

def get_system_logo():
    try:
        logo = SystemLogo.objects.latest('-created_at')
    except SystemLogo.DoesNotExist:
        logo = None
    return logo

class ToggleUserActiveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.user_type == UserType.ADMIN

    def post(self, request, user_uuid):
        user = User.objects.get(uuid=user_uuid)
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect('users:manage_users')

        user.is_active = not user.is_active
        user.save()
        action = "deactivated" if not user.is_active else "activated"
        messages.success(request, f"User {user.email} has been {action} successfully.")
        return redirect('users:manage_users')

class UserRegisterView(View):
    template_name = 'users/register.html'
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        logo = get_system_logo()
        contact = Contact.objects.first()
        context = {
            'logo': logo,
            'contact': contact,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        full_address = request.POST.get('full_address')
        mobile = request.POST.get('mobile')
        terms = request.POST.get('terms')

        errors = []
        if not all([full_name, full_address, email, mobile, password, terms]):
            errors.append("All fields are required.")
        if not mobile.isdigit() or len(mobile) != 10:
            errors.append("Enter a valid 10-digit mobile number.")
        if User.objects.filter(email=email).exists():
            errors.append("This email is already registered.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if not terms:
            messages.error(request, "You must accept the terms and conditions.")
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name, {
                "email": email,
                "full_name": full_name,
                "full_address": full_address,
                "mobile": mobile,
                'logo': get_system_logo(),
                'contact': Contact.objects.first(),
            })
        
        recaptcha_response = request.POST.get("g-recaptcha-response")
        recaptcha_secret = "6LfVFpUrAAAAAEYafcFU0DAmxaGrKIjaDmXG1_yP"
        recaptcha_verify_url = "https://www.google.com/recaptcha/api/siteverify"
        recaptcha_data = {"secret": recaptcha_secret, "response": recaptcha_response}
        recaptcha_result = requests.post(recaptcha_verify_url, data=recaptcha_data).json()

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
        contact = Contact.objects.first()
        return render(request, 'users/login.html', {'form': form, 'logo': logo, 'contact': contact})
    
    def post(self, request):
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None and user.is_active:
                login(request, user)
                return redirect("users:dashboard")
            elif user is not None and not user.is_active:
                messages.error(request, "Your account has been deactivated. Please contact the administrator.")
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid form submission.")
        
        logo = get_system_logo()
        contact = Contact.objects.first()
        return render(request, 'users/login.html', {'form': form, 'logo': logo, 'contact': contact})

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
        logo = get_system_logo()
        contact = Contact.objects.first()
        if request.user.user_type == UserType.ADMIN:
            return render(request, 'users/admin_password_change.html', {'form': form, 'logo': logo, 'contact': contact})
        return render(request, 'users/change_password.html', {'form': form, 'logo': logo, 'contact': contact})
    
    def post(self, request):
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        logo = get_system_logo()
        contact = Contact.objects.first()
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in after password change
            messages.success(request, "Password changed successfully.")
            return redirect("users:dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
        if request.user.user_type == UserType.ADMIN:
            return render(request, 'users/admin_password_change.html', {'form': form, 'logo': logo, 'contact': contact})
        return render(request, 'users/change_password.html', {'form': form, 'logo': logo, 'contact': contact})

@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        contact = Contact.objects.first()
        # Get feedback queryset based on user permissions
        if request.user.user_type == UserType.ADMIN:
            feedback_queryset = Feedback.objects.all()
        else:
            feedback_queryset = Feedback.objects.filter(
                Q(email=request.user.email) |
                Q(mobile=request.user.mobile) |
                Q(created_by=request.user) |
                Q(uuid__in=request.user.feedbacks.values_list('uuid', flat=True))
            ).distinct()

        # Calculate feedback statistics
        feedbacks = feedback_queryset.count()
        pending_feedbacks = feedback_queryset.filter(status='pending').count()
        solved_feedbacks = feedback_queryset.filter(status='solved').count()
        closed_feedbacks = feedback_queryset.filter(status='closed').count()
        reviewed_feedbacks = feedback_queryset.filter(status__in=['solved', 'closed']).count()
        
        # Calculate rating counts
        rating_counts = feedback_queryset.values('rating').annotate(count=Count('rating')).order_by('rating')
        rating_dict = {'excellent': 0, 'good': 0, 'poor': 0}
        for item in rating_counts:
            if item['rating'] in rating_dict:
                rating_dict[item['rating']] = item['count']

        context = {
            'users': User.objects.all().count() if request.user.user_type == UserType.ADMIN else None,
            'feedbacks': feedbacks,
            'pending_feedbacks': pending_feedbacks,
            'solved_feedbacks': solved_feedbacks,
            'closed_feedbacks': closed_feedbacks,
            'reviewed_feedbacks': reviewed_feedbacks,
            'excellent_feedbacks': rating_dict['excellent'],
            'good_feedbacks': rating_dict['good'],
            'poor_feedbacks': rating_dict['poor'],
            'logo': get_system_logo(),
            'contact': contact,
        }
        if request.user.user_type == UserType.ADMIN:
            return render(request, 'users/dashboard/admin_index.html', context)
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
        context['contact'] = Contact.objects.first()
        return context

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'users/profile.html'

    def get(self, request):
        user = request.user
        logo = get_system_logo()
        contact = Contact.objects.first()
        if request.user.user_type == UserType.ADMIN:
            return render(request, 'users/admin_profile.html', {'user': user, 'logo': logo, 'contact': contact})
        return render(request, self.template_name, {'user': user, 'logo': logo, 'contact': contact})

@method_decorator(login_required, name='dispatch')
class UpdateProfileView(View):
    def get_template_names(self) -> list[str]:
        if self.request.user.user_type == UserType.ADMIN:
            return ['users/admin_profile_update.html']
        return ['users/update_profile.html']

    def get(self, request):
        user = request.user
        logo = get_system_logo()
        contact = Contact.objects.first()
        return render(request, self.get_template_names(), {'user': user, 'logo': logo, 'contact': contact})
    
    def post(self, request):
        user = request.user
        profile_picture = request.FILES.get('profile_picture')
        logo = get_system_logo()
        contact = Contact.objects.first()
        if profile_picture:
            if user.profile_picture:
                default_storage.delete(user.profile_picture.path)
            user.profile_picture = profile_picture
            user.save()
            messages.success(request, "Profile picture updated successfully.")
            return redirect("users:dashboard")
        else:
            messages.error(request, "No profile picture uploaded.")
            return render(request, self.get_template_names(), {'user': user, 'logo': logo, 'contact': contact})

@method_decorator(login_required, name='dispatch')
class UserDeleteView(View):
    def post(self, request, user_uuid):
        user = User.objects.get(uuid=user_uuid)
        if user and request.user.user_type == UserType.ADMIN:
            if user != request.user:
                user.delete()
                messages.success(request, "User deleted successfully.")
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
        logo = get_system_logo()
        contact = Contact.objects.first()
        return render(request, self.template_name, {"logo": logo, 'contact': contact})
    
    def post(self, request):
        if request.user.user_type != UserType.ADMIN:
            messages.error(request, "You do not have permission to access this page.")
            return redirect("users:dashboard")
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        full_address = request.POST.get('full_address')
        mobile = request.POST.get('mobile')

        errors = []
        if not all([full_name, full_address, email, mobile, password]):
            errors.append("All fields are required.")
        if not mobile.isdigit() or len(mobile) != 10:
            errors.append("Enter a valid 10-digit mobile number.")
        if User.objects.filter(email=email).exists():
            errors.append("This email is already registered.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name, {
                "email": email,
                "full_name": full_name,
                "full_address": full_address,
                "mobile": mobile,
                'logo': get_system_logo(),
                'contact': Contact.objects.first(),
            })
        
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
        context['contact'] = Contact.objects.first()
        return context

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
            self.object.set_password(password)
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        context['contact'] = Contact.objects.first()
        return context

class ForgotPasswordView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        logo = get_system_logo()
        contact = Contact.objects.first()
        context = {
            'logo': logo,
            'contact': contact,
        }
        return render(request, 'users/forgot_password.html', context)

    def post(self, request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request, "User with this email does not exist.")
            return redirect("users:forgot_password")
        
        otp = f"{random.randint(100000, 999999)}"
        otp_record = PasswordResetOTP.objects.filter(user=user).order_by('-created_at').first()
        if otp_record:
            otp_record.otp = otp
            otp_record.save(update_fields=['otp', 'created_at', 'updated_at'])
        else:
            PasswordResetOTP.objects.create(user=user, otp=otp)

        send_otp_email(user.email, otp)
        messages.success(request, f"An OTP has been sent to {user.email}.")
        request.session['request_user_id'] = str(user.uuid)
        return redirect('users:verify_otp')

class VerifyOTPView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        logo = get_system_logo()
        contact = Contact.objects.first()
        context = {
            'logo': logo,
            'contact': contact,
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
        
        logo = get_system_logo()
        contact = Contact.objects.first()
        context = {
            'logo': logo,
            'contact': contact,
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

@method_decorator(login_required, name='dispatch')
class UpdateContactView(View):
    def test_func(self):
        return self.request.user.user_type == UserType.ADMIN

    def get(self, request):
        contact = Contact.objects.first()
        logo = get_system_logo()
        return render(request, 'users/update_contact.html', {'contact': contact, 'logo': logo})

    def post(self, request):
        if request.user.user_type != UserType.ADMIN:
            messages.error(request, "You do not have permission to update contact information.")
            return redirect("users:dashboard")
        
        contact = Contact.objects.first()
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        errors = []
        if not all([email, phone, address]):
            errors.append("All fields are required.")
        if not phone.isdigit() or len(phone) != 10:
            errors.append("Enter a valid 10-digit phone number.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'users/update_contact.html', {
                'contact': contact,
                'logo': get_system_logo(),
                'email': email,
                'phone': phone,
                'address': address,
            })

        if contact:
            contact.email = email
            contact.phone = phone
            contact.address = address
            contact.save()
        else:
            Contact.objects.create(email=email, phone=phone, address=address)
        
        messages.success(request, "Contact information updated successfully.")
        return redirect("users:dashboard")