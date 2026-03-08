from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms

class UserSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email','first_name','last_name','role','mobile_number','gender','password1','password2','unit_number']
        widgets = {
            'password1':forms.PasswordInput(),
            'password2':forms.PasswordInput(),
            'gender':forms.Select()
        }
        unit_number = forms.CharField(
            max_length=20,
            required=False,
            widget=forms.TextInput(attrs={"placeholder": "e.g. A-101 (residents only)"}),
        )
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.username = self.cleaned_data['email']  # if using email as username
        user.unit_number = self.cleaned_data.get('unit_number', '')
        if commit:
            user.save()
        return user
        
class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())