from django import forms
from .models import Invoice
from tenants.models import Tenant
from django.core.exceptions import ValidationError


class InvoiceForm(forms.ModelForm):
    class Meta:
       model = Invoice
       fields = (
           'rent_month',
           'date',
           'tenant',
           'house_number',
           'flat_number',
           'room_no',
           'building_name',
           'pan_or_vat_number',
           'rent_amount',
           'parking_fee',
           'electricity_fee',
           'security_fee',
           'drinking_water_fee',
           'generator_power_backup_fee',
           'normal_water_fee',
           'internet_telephone_tv_fee',
           'waste_fee',
            'other_fee',
           'discount',
           'total_amount',
           'tax',
           'grand_total',
           'previous_due',
           'bank_name',
           'account_number',
           'account_name',
           'owner_signature',
           'tenant_signature',
       )
       widgets = {
           'tenant': forms.Select(attrs={'class': 'form-control'}),
           'date': forms.DateInput(attrs={'type': 'date'}),
           'rent_month': forms.DateInput(attrs={'type': 'month'}),

       }

    def clean_rent_amount(self):
        rent_amount = self.cleaned_data.get('rent_amount')
        if rent_amount is not None and rent_amount <= 0:
            raise forms.ValidationError("Rent amount must be a positive number.")
        return rent_amount

    def clean_parking_fee(self):
        parking_fee = self.cleaned_data.get('parking_fee')
        if parking_fee is not None and parking_fee < 0:
            raise forms.ValidationError("Parking fee must be a non-negative number.")
        return parking_fee
    
    def clean_electricity_fee(self):
        electricity_fee = self.cleaned_data.get('electricity_fee')
        if electricity_fee is not None and electricity_fee < 0:
            raise forms.ValidationError("Electricity fee must be a non-negative number.")
        return electricity_fee
    
    def clean_security_fee(self):
        security_fee = self.cleaned_data.get('security_fee')
        if security_fee is not None and security_fee < 0:
            raise forms.ValidationError("Security fee must be a non-negative number.")
        return security_fee
    
    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is not None and discount < 0:
            raise forms.ValidationError("Discount must be a non-negative number.")
        return discount
    
    def clean_tax(self):
        tax = self.cleaned_data.get('tax')
        if tax is not None and tax < 0:
            raise forms.ValidationError("Tax must be a non-negative number.")
        return tax

    def clean_total_amount(self):
        total_amount = self.cleaned_data.get('total_amount')
        if total_amount is not None and total_amount < 0:
            raise forms.ValidationError("Total amount must be a non-negative number.")
        return total_amount

    def clean(self):
        cleaned_data = super().clean()
        
        rent_amount = cleaned_data.get('rent_amount', 0)
        parking_fee = cleaned_data.get('parking_fee', 0)
        electricity_fee = cleaned_data.get('electricity_fee', 0)
        security_fee = cleaned_data.get('security_fee', 0)
        drinking_water_fee = cleaned_data.get('drinking_water_fee', 0)
        generator_power_backup_fee = cleaned_data.get('generator_power_backup_fee', 0)
        normal_water_fee = cleaned_data.get('normal_water_fee', 0)
        internet_telephone_tv_fee = cleaned_data.get('internet_telephone_tv_fee', 0)
        waste_fee = cleaned_data.get('waste_fee', 0)
        other_fee = cleaned_data.get('other_fee', 0)
        previous_due = cleaned_data.get('previous_due', 0)
        discount = cleaned_data.get('discount', 0)
        tax = cleaned_data.get('tax', 0)

        # Ensure rent_amount and grand_total are properly calculated
        if rent_amount <= 0:
            raise ValidationError({"rent_amount": "Rent amount must be a positive number."})
        
        #calculate total_amount
        total_amount = (
            rent_amount +
            parking_fee +
            electricity_fee +
            security_fee +
            drinking_water_fee +
            generator_power_backup_fee +
            normal_water_fee +
            internet_telephone_tv_fee +
            waste_fee +
            other_fee 
        )

        # Calculate grand_total
        grand_total = total_amount + tax + previous_due - discount
        if grand_total < 0:
            raise ValidationError({"grand_total": "Grand total cannot be negative."})

        # Set the calculated grand_total back to the cleaned_data
        cleaned_data['grand_total'] = grand_total

        return cleaned_data

    

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)
        if user:
            self.fields['tenant'].queryset = Tenant.objects.filter(user=user)
