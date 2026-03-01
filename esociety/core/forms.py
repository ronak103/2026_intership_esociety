from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms

class UserSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email','first_name','last_name','role','mobile_number','gender','password1','password2']
        widgets = {
            'password1':forms.PasswordInput(),
            'password2':forms.PasswordInput(),
            'gender':forms.Select()
        }

        
class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())