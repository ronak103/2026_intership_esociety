from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Superusers are always active Admin — no pending, no blocked
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('status',   'active')   # ← never locked out
        extra_fields.setdefault('role',     'Admin')    # ← always Admin role

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    email = models.EmailField(unique=True)

    role_choice = (
        ('Admin',         'Admin'),
        ('Resident',      'Resident'),
        ('Securityguard', 'Securityguard'),
    )

    STATUS_CHOICES = (
        ('pending',  'Pending'),   # signed up, waiting for admin approval
        ('inactive', 'Inactive'),  # created but not yet OTP-verified
        ('active',   'Active'),
        ('blocked',  'Blocked'),
        ('deleted',  'Deleted'),
    )

    gender_choice = (('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other'))

    role          = models.CharField(max_length=20, choices=role_choice,   default='Resident')
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    is_admin      = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)
    first_name    = models.CharField(max_length=50,  blank=True, default='')
    last_name     = models.CharField(max_length=50,  blank=True, default='')
    gender        = models.CharField(max_length=10,  choices=gender_choice, default='Male')
    mobile_number = models.CharField(blank=True, default='')
    unit_number   = models.CharField(max_length=20,  blank=True, default='')
    joining_date  = models.DateField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class DemoBooking(models.Model):
    full_name    = models.CharField(max_length=100)
    mobile       = models.CharField(max_length=15)
    society_name = models.CharField(max_length=200)
    city         = models.CharField(max_length=100)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.society_name}"

    class Meta:
        ordering = ['-created_at']