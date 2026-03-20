from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.conf import settings


# ==============================
# VISITOR MODEL
# ==============================
class Visitor(models.Model):

    VISIT_TYPE = [
        ("guest", "Guest"),
        ("delivery", "Delivery"),
        ("maintenance", "Maintenance"),
        ("staff", "Staff"),
    ]

    APPROVAL_STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    ENTRY_STATUS = [
        ("waiting", "Waiting"),
        ("inside", "Inside"),
        ("exited", "Exited"),
        ("denied", "Denied"),
    ]

    REGISTERED_BY_CHOICES = [
        ("resident", "Resident"),
        ("Securityguard", "Securityguard"),
    ]

    visitor_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    visitor_type = models.CharField(max_length=20, choices=VISIT_TYPE)
    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="visitors",
        limit_choices_to={"role": "Resident"},
    )
    expected_date = models.DateField()
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default="pending")
    entry_status = models.CharField(max_length=20, choices=ENTRY_STATUS, default="waiting")
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    visitor_photo = models.ImageField(upload_to='visitor_photos/', null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, null=True, blank=True)
    guard = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="checked_visitors",
        limit_choices_to={"role": "Securityguard"},
    )
    registered_by = models.CharField(max_length=20, choices=REGISTERED_BY_CHOICES, default="Resident")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visitors"

    def __str__(self):
        return f"{self.visitor_name} visiting {self.resident.first_name} {self.resident.last_name}"


# ==============================
# COMPLAINT MODEL
# ==============================
class Complaint(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints",
        limit_choices_to={"role": "Resident"},
    )
    complaint_type = models.CharField(max_length=100)
    description = models.TextField()
    assigned_staff = models.CharField(max_length=100, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "complaints"

    def __str__(self):
        return self.complaint_type


# ==============================
# FACILITY MODEL
# ==============================
class Facility(models.Model):

    STATUS_CHOICES = [
        ("available", "Available"),
        ("unavailable", "Unavailable"),
    ]

    facility_name = models.CharField(max_length=100)
    description = models.TextField()
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    availability_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "facilities"

    def __str__(self):
        return self.facility_name


# ==============================
# FACILITY BOOKING
# ==============================
class FacilityBooking(models.Model):

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("completed", "Completed"),
    ]

    BOOKING_STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="bookings")
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="facility_bookings",
        limit_choices_to={"role": "Resident"},
    )
    booking_date = models.DateField()
    time_slot = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default="pending")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "facility_bookings"

    def __str__(self):
        return f"{self.facility.facility_name} - {self.booked_by.first_name} {self.booked_by.last_name}"


# ==============================
# PAYMENT MODEL
# ==============================
class Payment(models.Model):

    PAYMENT_TYPE = [
        ("maintenance", "Maintenance"),
        ("facility_booking", "Facility Booking"),
        ("other", "Other"),
    ]

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("completed", "Completed"),
    ]

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        limit_choices_to={"role": "Resident"},
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPE)
    payment_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="pending")
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"

    def __str__(self):
        return f"{self.payment_type} payment by {self.resident.first_name} {self.resident.last_name}"


# ==============================
# MAINTENANCE CONFIG  ← NEW
# Stores society-wide monthly due settings (singleton)
# ==============================
class MaintenanceConfig(models.Model):
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_day        = models.PositiveIntegerField(default=10)  # day of month dues are due
    updated_at     = models.DateTimeField(auto_now=True)
    updated_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    class Meta:
        db_table = "maintenance_config"

    def __str__(self):
        return f"₹{self.monthly_amount}/month — due by {self.due_day}th"

    @classmethod
    def get(cls):
        """Always returns the single config object, creates if not exists."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ==============================
# MAINTENANCE DUE  ← NEW
# One record per resident per month
# ==============================
class MaintenanceDue(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid",    "Paid"),
        ("overdue", "Overdue"),
        ("waived",  "Waived"),
    ]

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="maintenance_dues",
        limit_choices_to={"role": "Resident"},
    )
    amount    = models.DecimalField(max_digits=10, decimal_places=2)
    due_month = models.DateField()   # first day of month e.g. 2026-03-01
    due_date  = models.DateField()   # actual deadline e.g. 2026-03-10
    status    = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    paid_on   = models.DateField(null=True, blank=True)
    note      = models.TextField(null=True, blank=True)
    payment   = models.OneToOneField(   # links to Payment record when paid
        Payment,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="maintenance_due",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "maintenance_dues"
        unique_together = ("resident", "due_month")  # one due per resident per month
        ordering        = ["-due_month"]

    def __str__(self):
        return f"{self.resident.first_name} {self.resident.last_name} — {self.due_month.strftime('%b %Y')} — {self.status}"

    @property
    def is_overdue(self):
        from datetime import date
        return self.status == "pending" and date.today() > self.due_date


# ==============================
# NOTICE / ANNOUNCEMENT
# ==============================
class Notice(models.Model):

    TARGET_CHOICES = [
        ("all", "All"),
        ("resident", "Residents Only"),
        ("security", "Security Only"),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default="all")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "Admin"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notices"

    def __str__(self):
        return self.title


# ==============================
# NOTIFICATION MODEL
# ==============================
class Notification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"

    def __str__(self):
        return self.message


# ==============================
# EMERGENCY ALERT
# ==============================
class EmergencyAlert(models.Model):

    ALERT_TYPES = [
        ("fire", "Fire Alert"),
        ("medical", "Medical Emergency"),
        ("power", "Power Outage"),
        ("unauthorized", "Unauthorized Entry"),
    ]

    ALERT_STATUS = [
        ("active", "Active"),
        ("resolved", "Resolved"),
    ]

    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    message = models.TextField()
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    status = models.CharField(max_length=20, choices=ALERT_STATUS, default="active")
    action_taken = models.TextField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "emergency_alerts"

    def __str__(self):
        return self.alert_type


# ==============================
# COMMUNITY POLL
# ==============================
class Poll(models.Model):

    STATUS_CHOICES = [
        ("active", "Active"),
        ("closed", "Closed"),
    ]

    question = models.CharField(max_length=300)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "Admin"},
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "polls"

    def __str__(self):
        return self.question


class PollVote(models.Model):

    VOTE_CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
    ]

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="poll_votes",
        limit_choices_to={"role": "Resident"},
    )
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "poll_votes"
        unique_together = ("poll", "voter")

    def __str__(self):
        return f"{self.voter.first_name} {self.voter.last_name} voted {self.vote} on '{self.poll.question}'"