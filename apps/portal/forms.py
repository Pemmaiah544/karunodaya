from django import forms
from .models import Complaint
from apps.orders.models import Order


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
