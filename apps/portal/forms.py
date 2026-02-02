from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re
from .models import Complaint
from apps.orders.models import Order
from apps.core.validators import StrictEmailValidator


class ComplaintForm(forms.ModelForm):
    class MirrorOrderChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, obj):
            return f"Order #{obj.id} - {obj.get_order_type_display()} ({obj.created_at.strftime('%d %b %Y')})"

    order = MirrorOrderChoiceField(
        queryset=Order.objects.none(),
        required=False,
        empty_label="Not related to a specific order",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none'
        })
    )

    class Meta:
        model = Complaint
        fields = ['category', 'order', 'subject', 'description']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none',
                'placeholder': 'Briefly describe the issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none',
                'rows': 5,
                'placeholder': 'Provide more details about your concern'
            }),
        }

    def __init__(self, *args, **kwargs):
        parent = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)
        if parent:
            self.fields['order'].queryset = Order.objects.filter(parent=parent)


class RegisterForm(forms.Form):
    mobile_number = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[RegexValidator(r'^[6-9]\d{9}$', 'Mobile number must be 10 digits and start with 6-9')],
        widget=forms.TextInput(attrs={
            'placeholder': '10-digit mobile number',
            'class': 'w-full pl-16 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none',
            'pattern': '[6-9]{1}[0-9]{9}',
            'required': True,
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '');",
            'maxlength': '10'
        })
    )
    email = forms.EmailField(
        required=False,
        validators=[StrictEmailValidator()],
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address (optional)',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none',
            'pattern': r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$',
            'title': 'Enter a valid email address (e.g., user@example.com)',
        })
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none',
            'required': True
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none',
            'required': True
        })
    )

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get('mobile_number')
        if User.objects.filter(username=mobile_number).exists():
            raise ValidationError("This mobile number is already registered")
        return mobile_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:  # Only validate if email is provided
            email = email.lower()
            if User.objects.filter(email=email).exists():
                raise ValidationError("This email address is already registered")
            return email
        return ''  # Return empty string if no email provided

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must include at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must include at least one lowercase letter")
        if not re.search(r'\d', password):
            raise ValidationError("Password must include at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must include at least one special character")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            self.add_error('password2', "Passwords do not match")
        
        return cleaned_data


class PortalAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=10,
        validators=[RegexValidator(r'^[6-9]\d{9}$', 'Mobile number must be 10 digits and start with 6-9')],
        widget=forms.TextInput(attrs={
            'placeholder': '10-digit mobile number',
            'class': 'w-full pl-16 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none',
            'pattern': '[6-9]{1}[0-9]{9}',
            'required': True,
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '');",
            'maxlength': '10'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none',
            'required': True
        })
    )
