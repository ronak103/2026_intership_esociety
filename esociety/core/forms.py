from django import forms
from .models import User, DemoBooking


class UserSignupForm(forms.ModelForm):
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
        user.set_password(self.cleaned_data['password1'])
        user.status = 'inactive'
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


class DemoBookingForm(forms.ModelForm):
    class Meta:
        model = DemoBooking
        fields = ['full_name', 'mobile', 'society_name', 'city']
        widgets = {
            'full_name':    forms.TextInput(attrs={'class': 'cta-input', 'placeholder': 'Your full name'}),
            'mobile':       forms.TextInput(attrs={'class': 'cta-input', 'placeholder': 'Mobile number'}),
            'society_name': forms.TextInput(attrs={'class': 'cta-input', 'placeholder': 'Society name'}),
            'city':         forms.TextInput(attrs={'class': 'cta-input', 'placeholder': 'City / Pincode'}),
        }


# ── FORGOT PASSWORD FORMS ─────────────────────────────────

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your registered email',
            'autocomplete': 'email',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('No account found with this email address.')
        return email


class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'New password',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        }),
    )

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        if len(p1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return p2
        