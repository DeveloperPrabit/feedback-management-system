from .models import Tenant
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
import os

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            'name',
            'photo',
            'address',
            'mobile',
            'email',
            'profession',
            'house_name',
            'flat_number',
            'room_number',
            'rent_amount',
            'rent_start_date', 
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Name')}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Address')}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Mobile Number')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email Address')}),
            'profession': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Profession')}),
            'house_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('House Name')}),
            'flat_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Flat Number')}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Room Number')}),
            'rent_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Rent Amount')}),
            'rent_start_date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': _('Rent Start Date'), 'type': 'date'}),
        }
        error_messages = {
            'name': {
                'max_length': _("This name is too long."),
            },
            'email': {
                'invalid': _("Enter a valid email address."),
            },
            'mobile': {
                'invalid': _("Enter a valid mobile number."),
            },
            'rent_amount': {
                'invalid': _("Enter a valid rent amount."),
            },
        }

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not mobile:
            raise ValidationError(_("Mobile number is required."))
        if not mobile.isdigit():
            raise ValidationError(_("Mobile number must contain only digits."))
        if len(mobile) < 10 or len(mobile) > 15:
            raise ValidationError(_("Mobile number must be between 10 and 15 digits."))
        return mobile
    
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            # Get the file extension
            ext = os.path.splitext(photo.name)[1].lower()
            # Allowed file extensions
            allowed_extensions = ['.png', '.jpg', '.jpeg', '.pdf']
            if ext not in allowed_extensions:
                raise ValidationError(_("Only files with extensions PNG, JPG, JPEG, or PDF are allowed."))
        return photo


    

    