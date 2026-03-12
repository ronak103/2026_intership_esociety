from django import forms
from .models import Complaint,Visitor,Payment, FacilityBooking, Notice, Poll, Facility, PollVote, Notification
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


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

class VisitorForm(forms.ModelForm):

    class Meta:
        model = Visitor
        fields = [
            "visitor_name",
            "mobile_number",
            "visitor_type",
            "expected_date",
            "vehicle_number"
        ]

        widgets = {
            "visitor_name": forms.TextInput(attrs={
                "class": "inner-input",
                "placeholder": "Enter visitor name"
            }),

            "mobile_number": forms.TextInput(attrs={
                "class": "inner-input",
                "placeholder": "Enter mobile number"
            }),

            "visitor_type": forms.Select(attrs={
                "class": "inner-select"
            }),

            "expected_date": forms.DateInput(attrs={
                "class": "inner-input",
                "type": "date"
            }),

            "vehicle_number": forms.TextInput(attrs={
                "class": "inner-input",
                "placeholder": "Vehicle number (optional)"
            }),
        }

class GuardVisitorForm(forms.ModelForm):

    class Meta:
        model = Visitor
        fields = [
            "visitor_name",
            "mobile_number",
            "visitor_type",
            "vehicle_number",
            "resident",       # guard selects the resident being visited
        ]

        widgets = {
            "visitor_name": forms.TextInput(attrs={
                "class": "inner-input",
                "placeholder": "Enter visitor name"
            }),
            "mobile_number": forms.TextInput(attrs={
                "class": "inner-input",
                "placeholder": "Enter mobile number"
            }),
            "visitor_type": forms.Select(attrs={
                "class": "inner-select"
            }),
            "vehicle_number": forms.TextInput(attrs={
                "class": "inner-input",
                "placeholder": "Vehicle number (optional)"
            }),
            "resident": forms.Select(attrs={
                "class": "inner-select"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from core.models import User
        # Only show residents in the dropdown
        self.fields["resident"].queryset = User.objects.filter(role="Resident")
        self.fields["resident"].label = "Resident Being Visited"

class AdminAddResidentForm(forms.Form):
    """
    Plain Form (not ModelForm) because we call
    User.objects.create_user() manually in the view.
    Handles first/last name, email, unit, mobile, and password.
    """

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class":       "inner-input",
            "placeholder": "First name",
        }),
    )

    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class":       "inner-input",
            "placeholder": "Last name",
        }),
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class":       "inner-input",
            "placeholder": "email@example.com",
        }),
    )

    unit_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "class":       "inner-input",
            "placeholder": "e.g. A-101",
        }),
    )

    mobile_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            "class":       "inner-input",
            "placeholder": "e.g. 9876543210",
        }),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class":       "inner-input",
            "placeholder": "Set initial password",
        }),
    )

    def clean_password(self):
        pwd = self.cleaned_data.get("password", "")
        try:
            validate_password(pwd)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return pwd


# ──────────────────────────────────────────────────────────────
# ADMIN — COMPLAINT UPDATE
# ──────────────────────────────────────────────────────────────

class AdminComplaintUpdateForm(forms.ModelForm):
    """
    Admin-only form to update complaint status and assigned staff.
    Resident and other fields are not exposed here.
    """

    class Meta:
        model  = Complaint
        fields = ["status", "assigned_staff"]

        widgets = {
            "status": forms.Select(attrs={
                "class": "inner-select",
            }),
            "assigned_staff": forms.TextInput(attrs={
                "class":       "inner-input",
                "placeholder": "Name of assigned maintenance staff",
            }),
        }

        labels = {
            "assigned_staff": "Assigned Staff",
        }


# ──────────────────────────────────────────────────────────────
# ADMIN — PAYMENT
# ──────────────────────────────────────────────────────────────

class AdminPaymentForm(forms.ModelForm):
    """
    Admin records a payment on behalf of a resident.
    The resident FK queryset is restricted to role='resident'.
    """

    class Meta:
        model  = Payment
        fields = [
            "resident",
            "payment_type",
            "amount",
            "payment_date",
            "payment_status",
            "transaction_id",
        ]

        widgets = {
            "resident": forms.Select(attrs={
                "class": "inner-select",
            }),
            "payment_type": forms.Select(attrs={
                "class": "inner-select",
            }),
            "amount": forms.NumberInput(attrs={
                "class":       "inner-input",
                "placeholder": "e.g. 2500",
                "min":         "1",
                "step":        "0.01",
            }),
            "payment_date": forms.DateInput(attrs={
                "class": "inner-input",
                "type":  "date",
            }),
            "payment_status": forms.Select(attrs={
                "class": "inner-select",
            }),
            "transaction_id": forms.TextInput(attrs={
                "class":       "inner-input",
                "placeholder": "Optional",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import User
        self.fields["resident"].queryset = (
            User.objects.filter(role="Resident")
            .order_by("first_name", "last_name")
        )
        self.fields["resident"].label      = "Resident"
        self.fields["transaction_id"].required = False


# ──────────────────────────────────────────────────────────────
# ADMIN — NOTICE
# ──────────────────────────────────────────────────────────────

class AdminNoticeForm(forms.ModelForm):
    """
    Admin posts a notice/announcement.
    created_by is set automatically in the view, so excluded here.
    """

    class Meta:
        model  = Notice
        fields = ["title", "message", "target_audience"]

        widgets = {
            "title": forms.TextInput(attrs={
                "class":       "inner-input",
                "placeholder": "Notice title",
            }),
            "message": forms.Textarea(attrs={
                "class":       "inner-textarea",
                "rows":        4,
                "placeholder": "Write your announcement…",
            }),
            "target_audience": forms.Select(attrs={
                "class": "inner-select",
            }),
        }

        labels = {
            "target_audience": "Target Audience",
        }


# ──────────────────────────────────────────────────────────────
# ADMIN — POLL
# ──────────────────────────────────────────────────────────────

class AdminPollForm(forms.ModelForm):
    """
    Admin creates a community poll.
    created_by and status are set in the view.
    """

    class Meta:
        model  = Poll
        fields = ["question"]

        widgets = {
            "question": forms.TextInput(attrs={
                "class":       "inner-input",
                "placeholder": "e.g. Should we install CCTV in parking?",
            }),
        }

    def clean_question(self):
        question = self.cleaned_data.get("question", "").strip()
        if len(question) < 10:
            raise forms.ValidationError(
                "Poll question must be at least 10 characters long."
            )
        return question


# ──────────────────────────────────────────────────────────────
# ADMIN — FACILITY
# ──────────────────────────────────────────────────────────────

class AdminFacilityForm(forms.ModelForm):
    """
    Admin adds a new bookable facility.
    availability_status defaults to 'available' in the view.
    """

    class Meta:
        model  = Facility
        fields = ["facility_name", "description", "booking_fee"]

        widgets = {
            "facility_name": forms.TextInput(attrs={
                "class":       "inner-input",
                "placeholder": "e.g. Swimming Pool, Gym, Clubhouse",
            }),
            "description": forms.Textarea(attrs={
                "class":       "inner-textarea",
                "rows":        2,
                "placeholder": "Brief description of the facility",
            }),
            "booking_fee": forms.NumberInput(attrs={
                "class":       "inner-input",
                "placeholder": "0 for free",
                "min":         "0",
                "step":        "0.01",
            }),
        }

        labels = {
            "facility_name": "Facility Name",
            "booking_fee":   "Booking Fee (₹)",
        }

    def clean_booking_fee(self):
        fee = self.cleaned_data.get("booking_fee")
        if fee is None or fee < 0:
            raise forms.ValidationError("Booking fee cannot be negative.")
        return fee


# ──────────────────────────────────────────────────────────────
# ADMIN — CHANGE PASSWORD  (plain Form, not ModelForm)
# ──────────────────────────────────────────────────────────────

class AdminChangePasswordForm(forms.Form):
    """
    Lets the admin change their own password.
    Validation (current password check) is done in the view
    because we need access to request.user.
    """

    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            "class":       "inner-input",
            "placeholder": "Enter current password",
        }),
    )

    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "class":       "inner-input",
            "placeholder": "Enter new password",
        }),
    )

    confirm_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            "class":       "inner-input",
            "placeholder": "Confirm new password",
        }),
    )

    def clean_new_password(self):
        pwd = self.cleaned_data.get("new_password", "")
        try:
            validate_password(pwd)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return pwd

    def clean(self):
        cleaned = super().clean()
        new_pwd     = cleaned.get("new_password")
        confirm_pwd = cleaned.get("confirm_password")
        if new_pwd and confirm_pwd and new_pwd != confirm_pwd:
            raise forms.ValidationError(
                {"confirm_password": "New passwords do not match."}
            )
        return cleaned


# ──────────────────────────────────────────────────────────────
# ADMIN — SOCIETY SETTINGS  (plain Form, stored in session)
# ──────────────────────────────────────────────────────────────

class AdminSocietySettingsForm(forms.Form):
    """
    Stores basic society-wide configuration.
    Saved in request.session (or swap for a SocietySettings model).
    """

    society_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            "class":       "inner-input",
            "placeholder": "Enter society name",
        }),
    )

    total_units = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            "class":       "inner-input",
            "placeholder": "e.g. 120",
        }),
    )

    maintenance_fee = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class":       "inner-input",
            "placeholder": "e.g. 2500",
            "step":        "0.01",
        }),
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class":       "inner-textarea",
            "rows":        2,
            "placeholder": "Full address",
        }),
    )

    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            "class":       "inner-input",
            "placeholder": "admin@society.com",
        }),
    )

    contact_phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            "class":       "inner-input",
            "placeholder": "e.g. 9876543210",
        }),
    )