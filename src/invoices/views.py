from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from users.views import get_system_logo
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from datetime import datetime
from django.db.models import Q
from django.contrib import messages
from .models import Feedback
from .forms import FeedbackForm
from users.models import UserType
from django.conf import settings
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
import os
import logging
import random
import base64
from django.core.files.storage import default_storage
from io import BytesIO
from weasyprint import HTML, CSS

logger = logging.getLogger(__name__)

def get_feedback_serial_number():
    return ''.join(random.choices(datetime.now().strftime("%Y%m%d") + str(random.randint(1000, 9999)), k=10))

class FeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    context_object_name = 'feedbacks'
    paginate_by = 5
    ordering = ['-feedback_date']

    def get_queryset(self):
        queryset = super().get_queryset()
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
            queryset = queryset.filter(feedback_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(feedback_date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-feedback_date')
    
    def get_template_names(self):
        if self.request.user.user_type == UserType.ADMIN:
            return ['invoices/feedback_list.html']
        return ['invoices/user_feedback_list.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        context['debug'] = getattr(settings, 'DEBUG', False)
        return context

class ManageFeedbacksView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = 'invoices/manage_feedbacks.html'
    context_object_name = 'feedbacks'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
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
            queryset = queryset.filter(feedback_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(feedback_date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-feedback_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logo'] = get_system_logo()
        context['debug'] = getattr(settings, 'DEBUG', False)
        return context

class FeedbackCreateView(View):
    template_name = 'invoices/create_invoice.html'

    def get(self, request, *args, **kwargs):
        feedback_uuid = request.GET.get('feedback_uuid')
        logo = get_system_logo()

        if feedback_uuid:
            try:
                feedback = Feedback.objects.get(uuid=feedback_uuid)
                form = FeedbackForm(instance=feedback, initial={
                    'name': feedback.name or request.user.full_name if request.user.is_authenticated else '',
                    'anonymous': feedback.anonymous
                })
            except Feedback.DoesNotExist:
                messages.error(request, "Feedback link is invalid.")
                form = FeedbackForm(initial={'name': request.user.full_name if request.user.is_authenticated else ''})
        else:
            initial_data = {
                'feedback_date': datetime.now().date(),
                'name': request.user.full_name if request.user.is_authenticated else '',
                'anonymous': False
            }
            if request.user.is_authenticated:
                initial_data.update({
                    'email': request.user.email,
                    'mobile': request.user.mobile or '',
                    'address': request.user.full_address or '',
                })
            form = FeedbackForm(initial=initial_data)

        return render(request, self.template_name, {'form': form, 'logo': logo, 'feedback_uuid': feedback_uuid})

    def post(self, request, *args, **kwargs):
        feedback_uuid = request.GET.get('feedback_uuid')
        logo = get_system_logo()

        if feedback_uuid:
            try:
                feedback = Feedback.objects.get(uuid=feedback_uuid)
                form = FeedbackForm(request.POST, request.FILES, instance=feedback)
            except Feedback.DoesNotExist:
                messages.error(request, "Feedback link is invalid.")
                form = FeedbackForm(request.POST, request.FILES)
        else:
            form = FeedbackForm(request.POST, request.FILES)

        if form.is_valid():
            feedback = form.save(commit=False)
            if not feedback_uuid:
                feedback.serial_number = get_feedback_serial_number()
                if request.user.is_authenticated:
                    feedback.created_by = request.user
            feedback.save()
            messages.success(request, "Feedback submitted successfully!")
            return redirect('invoices:view_feedbacks')
        else:
            messages.error(request, f"Form Error: {form.errors}")
            return render(request, self.template_name, {'form': form, 'logo': logo, 'feedback_uuid': feedback_uuid})

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
        return context

def download_feedback_pdf(request, feedback_uuid):
    try:
        feedback = get_object_or_404(Feedback, uuid=feedback_uuid)
        generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logo = get_system_logo()

        logo_base64 = None
        if logo and hasattr(logo, 'logo') and logo.logo:
            try:
                with default_storage.open(logo.logo.name, 'rb') as f:
                    logo_data = f.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
            except Exception as e:
                logger.error(f"Error encoding logo to Base64: {str(e)}")
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
            'generated_date': generated_date,
            'office_name': request.user.full_name if request.user.is_authenticated else "Your Office",
        })

        pdf_buffer = BytesIO()
        HTML(string=html_string).write_pdf(
            target=pdf_buffer,
            stylesheets=[CSS(string='''
                @font-face {
                    font-family: 'NotoSansDevanagari';
                    src: url('https://fonts.gstatic.com/s/notosansdevanagari/v28/TuGfUUFzXI5FBtUyc7k8yVLSAY6c2CwLq6M-5ZDcY8fGzvO.svg#NotoSansDevanagari') format('svg');
                }
                body { font-family: 'NotoSansDevanagari', Arial, sans-serif; }
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