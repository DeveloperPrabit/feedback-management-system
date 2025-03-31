from .models import Tenant
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone

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
        help_texts = {
            'name': _('Enter the name of the tenant.'),
            'photo': _('Upload a photo of the tenant.'),
            'address': _('Enter the address of the tenant.'),
            'mobile': _('Enter the mobile number of the tenant.'),
            'email': _('Enter the email address of the tenant.'),
            'profession': _('Enter the profession of the tenant.'),
            'house_name': _('Enter the house name of the tenant.'),
            'flat_number': _('Enter the flat number of the tenant.'),
            'room_number': _('Enter the room number of the tenant.'),
            'rent_amount': _('Enter the rent amount for the tenant.'),
            'rent_start_date': _('Select the date when rent starts for this tenant.'), 
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
            raise ValidationError(_('Mobile number is required.'))
        return mobile
    