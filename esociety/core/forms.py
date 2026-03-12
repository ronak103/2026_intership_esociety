from django import forms
from .models import User


class UserSignupForm(forms.ModelForm):
    """
    Signup form based directly on the custom User model.
    Avoids UserCreationForm which is tied to Django's default username-based User.
    """

    # Defined at class level (not inside Meta) so Django renders and validates them
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model  = User
        fields = [
            'first_name', 'last_name', 'email',
            'gender', 'mobile_number', 'unit_number', 'role',
        ]
        widgets = {
            'first_name':    forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name':     forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email':         forms.EmailInput(attrs={'placeholder': 'Email Address', 'autocomplete': 'email'}),
            'mobile_number': forms.TextInput(attrs={'placeholder': 'Mobile Number'}),
            'unit_number':   forms.TextInput(attrs={'placeholder': 'e.g. A-101 (residents only)'}),
            'gender':        forms.Select(),
            'role':          forms.Select(),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        if len(p1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])  # hashes the password properly
        user.status = 'inactive'   # always start inactive — required for OTP verification flow
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'autocomplete': 'email'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'autocomplete': 'current-password'}),
    )