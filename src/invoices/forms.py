from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    RATING_CHOICES = (
        ('excellent', 'उत्कृष्ट Excellent'),
        ('good', 'राम्रो Good'),
        ('poor', 'नराम्रो Poor'),
    )
    rating = forms.ChoiceField(choices=RATING_CHOICES, widget=forms.RadioSelect(attrs={'class': 'radio-group'}))

    class Meta:
        model = Feedback
        fields = [
            'name', 'address', 'mobile', 'email', 'rating',
            'feedback_text', 'attachment', 'anonymous', 'feedback_date'
        ]
        widgets = {
            'feedback_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'feedback_text': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'anonymous': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')], attrs={'class': 'radio-group'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # Existing feedback
            self.fields['anonymous'].initial = self.instance.anonymous
        if 'data' in kwargs and kwargs['data'].get('anonymous') == 'True':
            self.fields['name'].required = False
            self.fields['address'].required = False
            self.fields['mobile'].required = False
            self.fields['email'].required = False
        else:
            self.fields['name'].required = True
            self.fields['address'].required = True
            self.fields['mobile'].required = True
            self.fields['email'].required = False

    def clean(self):
        cleaned_data = super().clean()
        anonymous = cleaned_data.get('anonymous')
        if anonymous:
            cleaned_data['name'] = None
            cleaned_data['address'] = None
            cleaned_data['mobile'] = None
            cleaned_data['email'] = None
        return cleaned_data