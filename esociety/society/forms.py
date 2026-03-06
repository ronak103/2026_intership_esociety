
from django import forms
from .models import Complaint


class ComplaintForm(forms.ModelForm):

    class Meta:
        model = Complaint
        fields = ["complaint_type", "description", "priority"]

        widgets = {
            "complaint_type": forms.TextInput(attrs={
                "class": "inner-input",
                "placeholder": "Complaint type (e.g. Plumbing, Electricity)"
            }),

            "description": forms.Textarea(attrs={
                "class": "inner-textarea",
                "rows": 3,
                "placeholder": "Describe your issue"
            }),

            "priority": forms.Select(attrs={
                "class": "inner-select"
            })
        }