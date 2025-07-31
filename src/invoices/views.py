from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse, JsonResponse
from users.views import get_system_logo
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib import messages
from .models import Feedback
from .forms import FeedbackForm
from users.models import UserType, User, Contact
from django.conf import settings
from django.views.decorators.http import require_POST
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from captcha.views import captcha_refresh
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
import os
import logging
import base64
from django.core.files.storage import default_storage
from io import BytesIO
from weasyprint import HTML, CSS
from django.contrib.auth.mixins import UserPassesTestMixin
from datetime import datetime
import random
import uuid
import openpyxl

logger = logging.getLogger(__name__)

@csrf_exempt
def custom_captcha_refresh(request):
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logger.error("Non-AJAX request to captcha refresh")
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        if CaptchaStore.objects.count() == 0:
            logger.warning("No CAPTCHA entries found, generating new one")
            key = CaptchaStore.generate_key()
            logger.debug(f"Generated new CAPTCHA key: {key}")
        response = captcha_refresh(request)
        logger.debug(f"CAPTCHA refresh response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in custom_captcha_refresh: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Failed to refresh CAPTCHA'}, status=500)

def custom_404(request, exception):
    logger.debug(f"Rendering 404.html for request: {request.path}, exception: {str(exception)}")
    return render(request, '404.html', status=404)

def get_feedback_serial_number():
    return ''.join(random.choices(datetime.now().strftime("%Y%m%d") + str(random.randint(1000, 9999)), k=10))

class FeedbackCreateView(View):
    def get(self, request, user_id=None, *args, **kwargs):
        logger.debug(f"FeedbackCreateView.get: path={request.path}, user_id={user_id}, is_authenticated={request.user.is_authenticated}, user_uuid={request.user.uuid if request.user.is_authenticated else None}")

        if request.user.is_authenticated:
            current_uuid = str(request.user.uuid)
            requested_uuid = str(user_id) if user_id else None
            logger.debug(f"Comparing requested_uuid={requested_uuid} with current_uuid={current_uuid}")
            if requested_uuid != current_uuid:
                logger.debug(f"Redirecting authenticated user to /create-feedback/{current_uuid}/")
                return redirect('invoices:create_feedback_with_user', user_id=request.user.uuid)

        form = FeedbackForm(user=request.user if request.user.is_authenticated else None)
        creator = None
        creator_profile_picture = None
        creator_name = None
        reviewed_feedbacks = 0

        if user_id:
            try:
                creator = User.objects.get(uuid=user_id)
                creator_profile_picture = creator.profile_picture.url if hasattr(creator, 'profile_picture') and creator.profile_picture else None
                creator_name = creator.full_name or creator.email
                feedback_queryset = Feedback.objects.filter(
                    Q(created_by=creator) |
                    Q(uuid__in=creator.feedbacks.values_list('uuid', flat=True))
                ).distinct()
                reviewed_feedbacks = feedback_queryset.filter(status__in=['solved', 'closed']).count()
            except User.DoesNotExist:
                logger.error(f"User with uuid={user_id} not found")
                messages.error(request, "Invalid user ID in the shared link.", extra_tags='create_feedback')
                return redirect('users:login')

        context = {
            'form': form,
            'logo': get_system_logo(),
            'user_id': user_id,
            'creator_profile_picture': creator_profile_picture,
            'creator_name': creator_name,
            'creator': creator,
            'success_message': None,
            'reviewed_feedbacks': reviewed_feedbacks,
            'contact': Contact.objects.first(),
        }
        logger.debug(f"Rendering create_invoice.html with context: {context}")
        return render(request, 'invoices/create_invoice.html', context)

    def post(self, request, user_id=None, *args, **kwargs):
        form = FeedbackForm(request.POST, request.FILES, user=request.user if request.user.is_authenticated else None)
        creator = None
        creator_profile_picture = None
        creator_name = None
        reviewed_feedbacks = 0

        if user_id:
            try:
                creator = User.objects.get(uuid=user_id)
                creator_profile_picture = creator.profile_picture.url if hasattr(creator, 'profile_picture') and creator.profile_picture else None
                creator_name = creator.full_name or creator.email
                feedback_queryset = Feedback.objects.filter(
                    Q(created_by=creator) |
                    Q(uuid__in=creator.feedbacks.values_list('uuid', flat=True))
                ).distinct()
                reviewed_feedbacks = feedback_queryset.filter(status__in=['solved', 'closed']).count()
            except User.DoesNotExist:
                logger.error(f"User with uuid={user_id} not found")
                messages.error(request, "Invalid user ID in the shared link.", extra_tags='create_feedback')
                return redirect('users:login')

        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.serial_number = get_feedback_serial_number()
            if creator:
                feedback.created_by = creator
            if request.user.is_authenticated and not user_id:
                feedback.created_by = request.user
            feedback.save()

            messages.success(request, "तपाईको अमुल्य सुझावको लागि धन्यबाद । सुझावको बिवरण जाँच गरी आवस्यक प्रकृयामा जानेछौ ।", extra_tags='create_feedback success')
            if user_id and not request.user.is_authenticated:
                return redirect('users:login')
            return redirect('invoices:view_feedbacks')
        else:
            messages.error(request, "Please correct the errors below.", extra_tags='create_feedback')

        context = {
            'form': form,
            'logo': get_system_logo(),
            'user_id': user_id,
            'creator_profile_picture': creator_profile_picture,
            'creator_name': creator_name,
            'creator': creator,
            'success_message': messages.get_messages(request),
            'reviewed_feedbacks': reviewed_feedbacks,
            'contact': Contact.objects.first(),
        }
        return render(request, 'invoices/create_invoice.html', context)

class FeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    context_object_name = 'feedbacks'
    paginate_by = 5
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('created_by')
        search = self.request.GET.get('search', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        status = self.request.GET.get('status', '')

        if self.request.user.user_type == UserType.ADMIN:
            queryset = Feedback.objects.all()
        else:
            queryset = Feedback.objects.filter(
                Q(email=self.request.user.email) |
                Q(mobile=self.request.user.mobile) |
                Q(created_by=self.request.user) |
                Q(uuid__in=self.request.user.feedbacks.values_list('uuid', flat=True))
            ).distinct()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile__icontains=search) |
                Q(address__icontains=search) |
                Q(feedback_text__icontains=search) |
                Q(serial_number__icontains=search)
            ).distinct()

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

    def get_template_names(self):
        if self.request.user.user_type == UserType.ADMIN:
            return ['invoices/feedback_list.html']
        return ['invoices/user_feedback_list.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        context['debug'] = getattr(settings, 'DEBUG', False)
        context['search'] = self.request.GET.get('search', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['status'] = self.request.GET.get('status', '')
        context['contact'] = Contact.objects.first()
        return context

class ManageFeedbacksView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = 'invoices/manage_feedbacks.html'
    context_object_name = 'feedbacks'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset().select_related('created_by')
        search = self.request.GET.get('search', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        status = self.request.GET.get('status', '')

        if self.request.user.user_type == UserType.ADMIN:
            queryset = Feedback.objects.all()
        else:
            queryset = Feedback.objects.filter(
                Q(email=self.request.user.email) |
                Q(mobile=self.request.user.mobile) |
                Q(created_by=self.request.user) |
                Q(uuid__in=self.request.user.feedbacks.values_list('uuid', flat=True))
            ).distinct()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile__icontains=search) |
                Q(address__icontains=search) |
                Q(feedback_text__icontains=search) |
                Q(serial_number__icontains=search)
            ).distinct()

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        context['debug'] = getattr(settings, 'DEBUG', False)
        context['search'] = self.request.GET.get('search', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['status'] = self.request.GET.get('status', '')
        context['contact'] = Contact.objects.first()
        return context

class FeedbackDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        feedbacks = self.get_queryset()
        if not feedbacks:
            messages.error(request, "No feedbacks found for the given criteria.")
            return redirect('invoices:view_feedbacks')

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="feedbacks.xlsx"'

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Feedbacks'

        headers = ['Serial Number', 'Name', 'Email', 'Mobile', 'Address', 'Rating', 'Feedback Text', 'Status', 'Created At']
        worksheet.append(headers)

        for feedback in feedbacks:
            name = "Anonymous" if feedback.anonymous else feedback.name or "N/A"
            worksheet.append([
                feedback.serial_number,
                name,
                feedback.email or "N/A",
                feedback.mobile or "N/A",
                feedback.address or "N/A",
                feedback.get_rating_display(),
                feedback.feedback_text,
                feedback.get_status_display(),
                feedback.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        workbook.save(response)
        return response

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        status = self.request.GET.get('status', '')

        if self.request.user.user_type == UserType.ADMIN:
            queryset = Feedback.objects.all()
        else:
            queryset = Feedback.objects.filter(
                Q(email=self.request.user.email) |
                Q(mobile=self.request.user.mobile) |
                Q(created_by=self.request.user) |
                Q(uuid__in=self.request.user.feedbacks.values_list('uuid', flat=True))
            ).distinct()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile__icontains=search) |
                Q(address__icontains=search) |
                Q(feedback_text__icontains=search) |
                Q(serial_number__icontains=search)
            ).distinct()

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

class FeedbackDetailView(DetailView):
    model = Feedback
    template_name = 'invoices/feedback_detail.html'
    context_object_name = 'feedback'
    pk_url_kwarg = 'feedback_uuid'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.user_type == UserType.ADMIN:
                return Feedback.objects.all()
            else:
                return Feedback.objects.filter(
                    Q(email=self.request.user.email) |
                    Q(mobile=self.request.user.mobile) |
                    Q(created_by=self.request.user) |
                    Q(uuid__in=self.request.user.feedbacks.values_list('uuid', flat=True))
                ).distinct()
        else:
            return Feedback.objects.filter(uuid=self.kwargs['feedback_uuid'])

    def get_template_names(self):
        if self.request.user.is_authenticated and self.request.user.user_type == UserType.ADMIN:
            return ['invoices/feedback_detail.html']
        return ['invoices/user_feedback_detail.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedback = self.get_object()
        context['logo'] = get_system_logo()
        context['debug'] = getattr(settings, 'DEBUG', False)
        context['pdf_url'] = self.request.build_absolute_uri(
            reverse_lazy('invoices:download_feedback', kwargs={'feedback_uuid': feedback.uuid})
        )
        context['contact'] = Contact.objects.first()
        return context

def download_feedback_pdf(request, feedback_uuid):
    try:
        feedback = get_object_or_404(Feedback, uuid=feedback_uuid)
        generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logo = get_system_logo()
        logo_base64 = None
        profile_picture_base64 = None
        creator = None

        # Fetch creator if user_id exists or use authenticated user
        if feedback.created_by:
            creator = feedback.created_by
        elif request.user.is_authenticated:
            creator = request.user

        # Handle profile picture as base64
        if creator and hasattr(creator, 'profile_picture') and creator.profile_picture:
            try:
                with default_storage.open(creator.profile_picture.name, 'rb') as f:
                    profile_picture_data = f.read()
                    profile_picture_base64 = base64.b64encode(profile_picture_data).decode('utf-8')
            except Exception as e:
                logger.error(f"Error encoding profile picture to base64: {str(e)}")

        # Fallback to system logo if profile picture is not available
        if not profile_picture_base64:
            if logo and hasattr(logo, 'logo') and logo.logo:
                try:
                    with default_storage.open(logo.logo.name, 'rb') as f:
                        logo_data = f.read()
                        logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                except Exception as e:
                    logger.error(f"Error encoding logo to base64: {str(e)}")
            else:
                try:
                    with open(os.path.join(settings.STATIC_ROOT, 'images/logo.jpeg'), 'rb') as f:
                        logo_data = f.read()
                        logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                except FileNotFoundError:
                    logger.error("Static logo file (images/logo.jpeg) not found")

        html_string = render_to_string('invoices/feedback_pdf.html', {
            'feedback': feedback,
            'logo_base64': logo_base64,
            'profile_picture_base64': profile_picture_base64,
            'generated_date': generated_date,
            'office_name': request.user.full_name if request.user.is_authenticated else "Your Office",
            'contact': Contact.objects.first(),
            'creator': creator,
        })

        pdf_buffer = BytesIO()
        HTML(string=html_string).write_pdf(
            target=pdf_buffer,
            stylesheets=[CSS(string='''
                body { font-family: Arial, sans-serif; }
            ''')]
        )
        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="feedback_{feedback.serial_number}.pdf"'
        return response
    except Exception as e:
        logger.error(f"Exception in download_feedback_pdf: {str(e)}")
        return HttpResponse(f'Exception occurred: {str(e)}')

@login_required
@require_POST
def update_status(request, feedback_uuid):
    if request.user.user_type == UserType.ADMIN:
        feedback = get_object_or_404(Feedback, uuid=feedback_uuid)
    else:
        feedback = get_object_or_404(
            Feedback.objects.filter(
                Q(uuid=feedback_uuid) & (
                    Q(email=request.user.email) |
                    Q(mobile=request.user.mobile) |
                    Q(created_by=request.user) |
                    Q(uuid__in=request.user.feedbacks.values_list('uuid', flat=True))
                )
            )
        )

    new_status = request.POST.get('status')
    if new_status in ['pending', 'solved', 'closed']:
        feedback.status = new_status
        feedback.save()
        messages.success(request, f"Feedback status updated to {new_status.title()}.")
    else:
        messages.error(request, "Invalid status.")
    return redirect('invoices:view_feedbacks')

class DeleteFeedbackView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.user_type == UserType.ADMIN

    def post(self, request, feedback_uuid):
        feedback = get_object_or_404(Feedback, uuid=feedback_uuid)
        feedback.delete()
        messages.success(request, "Feedback deleted successfully.")
        return redirect('invoices:view_feedbacks')

class ClaimFeedbackView(LoginRequiredMixin, View):
    def post(self, request, feedback_uuid):
        feedback = get_object_or_404(Feedback, uuid=feedback_uuid)
        if feedback.created_by is None and (feedback.email == request.user.email or feedback.mobile == request.user.mobile):
            feedback.created_by = request.user
            feedback.save()
            messages.success(request, "Feedback claimed successfully.")
        else:
            messages.error(request, "You cannot claim this feedback.")
        return redirect('invoices:view_feedbacks')