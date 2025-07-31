from django import forms
from .models import Feedback
from captcha.fields import CaptchaField

class FeedbackForm(forms.ModelForm):
    RATING_CHOICES = (
        ('excellent', 'उत्कृष्ट'),
        ('good', 'राम्रो'),
        ('poor', 'नराम्रो'),
    )

    rating = forms.ChoiceField(choices=RATING_CHOICES, widget=forms.RadioSelect(attrs={'class': 'radio-group'}))
    captcha = CaptchaField()

    class Meta:
        model = Feedback
        fields = [
            'name', 'address', 'mobile', 'email', 'rating',
            'feedback_text', 'attachment', 'anonymous', 'captcha'
        ]
        widgets = {
            'feedback_text': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'anonymous': forms.RadioSelect(choices=[(True, 'हो'), (False, 'होइन')], attrs={'class': 'radio-group'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['name'].initial = user.full_name
        if self.instance.pk:
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