from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

import threading
import random
import string
import os
import logging

from .forms import UserSignupForm, UserLoginForm, DemoBookingForm
from .models import User, DemoBooking

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────
OTP_EXPIRY_SECONDS = 5 * 60   # 5 minutes
OTP_MAX_ATTEMPTS   = 5


def home(request):
    form = DemoBookingForm()
    return render(request, "home.html",{'form': form})

# ════════════════════════════════════════════════════════
#  SESSION-BASED OTP FUNCTIONS  (no model / no DB table)
# ════════════════════════════════════════════════════════

def generate_otp():
    """Return a cryptographically random 6-digit string."""
    return ''.join(random.choices(string.digits, k=6))


def store_otp_in_session(request, user_id, otp_code):
    """Write OTP state into the signed/encrypted session."""
    request.session['otp'] = {
        'user_id':    user_id,
        'code':       otp_code,
        'created_at': timezone.now().isoformat(),
        'attempts':   0,
        'is_used':    False,
    }
    request.session.modified = True


def get_otp_from_session(request):
    return request.session.get('otp')


def clear_otp_from_session(request):
    request.session.pop('otp', None)
    request.session.modified = True


def is_otp_expired(otp_data):
    created_at = timezone.datetime.fromisoformat(otp_data['created_at'])
    if timezone.is_naive(created_at):
        created_at = timezone.make_aware(created_at)
    return timezone.now() > created_at + timezone.timedelta(seconds=OTP_EXPIRY_SECONDS)


def check_otp(request, submitted_code):
    """
    Validate OTP from session.
    Returns (success: bool, error_message: str | None).
    """
    otp_data = get_otp_from_session(request)

    if not otp_data:
        return False, 'Session expired. Please log in again.'

    if otp_data.get('is_used'):
        return False, 'OTP already used. Please request a new one.'

    if is_otp_expired(otp_data):
        clear_otp_from_session(request)
        return False, 'OTP has expired. Please log in again to receive a new one.'

    if otp_data.get('attempts', 0) >= OTP_MAX_ATTEMPTS:
        clear_otp_from_session(request)
        return False, 'Too many incorrect attempts. Please log in again.'

    if otp_data['code'] != submitted_code.strip():
        otp_data['attempts'] += 1
        request.session['otp'] = otp_data
        request.session.modified = True
        remaining = OTP_MAX_ATTEMPTS - otp_data['attempts']
        if remaining > 0:
            return False, f'Incorrect OTP. {remaining} attempt(s) remaining.'
        clear_otp_from_session(request)
        return False, 'Too many incorrect attempts. Please log in again.'

    # ✅ Correct — mark as used to prevent replay
    otp_data['is_used'] = True
    request.session['otp'] = otp_data
    request.session.modified = True
    return True, None


# ════════════════════════════════════════════════════════
#  EMAIL HELPERS
# ════════════════════════════════════════════════════════

def _send_otp_email(user, otp_code):
    """Fire-and-forget OTP email in a daemon thread."""
    def _send():
        try:
            html = render_to_string('core/otp_email.html', {
                'first_name': user.first_name or user.email,
                'otp_code':   otp_code,
                'expiry_min': OTP_EXPIRY_SECONDS // 60,
            })
            msg = EmailMultiAlternatives(
                subject='Your E-Society Login OTP',
                body=otp_code,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email],
            )
            msg.attach_alternative(html, 'text/html')
            msg.send()
        except Exception as exc:
            logger.exception('OTP email failed for %s: %s', user.email, exc)

    threading.Thread(target=_send, daemon=True).start()


def _send_welcome_email(user):
    """Fire-and-forget welcome email in a daemon thread."""
    def _send():
        try:
            html = render_to_string('core/welcome_email.html', {
                'first_name': user.first_name or user.email,
            })
            msg = EmailMultiAlternatives(
                subject='Welcome to E-Society',
                body='Welcome to E-Society',
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email],
            )
            msg.attach_alternative(html, 'text/html')
            image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'welcome.png')
            if os.path.exists(image_path):
                msg.attach_file(image_path)
            msg.send()
        except Exception as exc:
            logger.exception('Welcome email failed for %s: %s', user.email, exc)

    threading.Thread(target=_send, daemon=True).start()


# ════════════════════════════════════════════════════════
#  SHARED HELPERS
# ════════════════════════════════════════════════════════

def _redirect_by_role(user):
    return redirect({
        'Admin':         'admin_dashboard',
        'Resident':      'resident_dashboard',
        'Securityguard': 'security_dashboard',
    }.get(user.role, 'home'))


def _auth_render(request, login_form, signup_form, active_form):
    return render(request, 'core/auth.html', {
        'login_form':  login_form,
        'signup_form': signup_form,
        'active_form': active_form,
    })


# ════════════════════════════════════════════════════════
#  VIEWS
# ════════════════════════════════════════════════════════

@never_cache
def userSignupView(request):
    signup_form = UserSignupForm(request.POST or None)
    login_form  = UserLoginForm()
    active_form = 'signup'

    if request.method == 'POST' and signup_form.is_valid():
        user = signup_form.save()          # status = 'inactive' by default
        _send_welcome_email(user)
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')

    return _auth_render(request, login_form, signup_form, active_form)


@never_cache
def userLoginview(request):
    login_form  = UserLoginForm(request.POST or None)
    signup_form = UserSignupForm()
    active_form = 'signin'

    if request.method == 'POST' and login_form.is_valid():
        email    = login_form.cleaned_data['email']
        password = login_form.cleaned_data['password']

        # 1. Lookup user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Account does not exist.')
            return _auth_render(request, login_form, signup_form, active_form)

        # 2. Password check
        if not user.check_password(password):
            messages.error(request, 'Invalid email or password.')
            return _auth_render(request, login_form, signup_form, active_form)

        # 3. Status gate
        if user.status == 'deleted':
            messages.error(request, 'Account does not exist.')
            return _auth_render(request, login_form, signup_form, active_form)

        if user.status == 'blocked':
            messages.error(request, 'Your account has been blocked. Please contact support.')
            return _auth_render(request, login_form, signup_form, active_form)

        if user.status == 'active':
            login(request, user)
            return _redirect_by_role(user)

        # 4. Inactive → send OTP
        otp_code = generate_otp()
        store_otp_in_session(request, user.pk, otp_code)
        _send_otp_email(user, otp_code)
        messages.info(request, f'A 6-digit OTP has been sent to {user.email}. It expires in {OTP_EXPIRY_SECONDS // 60} minutes.')
        return redirect('verify_otp')

    return _auth_render(request, login_form, signup_form, active_form)


@never_cache
def LogoutView(request):
    logout(request)
    return redirect('login')


@never_cache
def verifyOtpView(request):
    otp_data = get_otp_from_session(request)
    if not otp_data:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    try:
        user = User.objects.get(pk=otp_data['user_id'])
    except User.DoesNotExist:
        clear_otp_from_session(request)
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login')

    if request.method == 'POST':
        # Accept either a single 'otp' field OR six individual 'otp1'…'otp6' fields
        if request.POST.get('otp'):
            submitted = request.POST.get('otp', '').strip()
        else:
            digits = [request.POST.get(f'otp{i}', '').strip() for i in range(1, 7)]
            submitted = ''.join(digits)

        if len(submitted) != 6 or not submitted.isdigit():
            messages.error(request, 'Please enter all 6 digits of the OTP.')
            return render(request, 'core/verify_otp.html', {'email': user.email})

        success, error_msg = check_otp(request, submitted)

        if success:
            user.status = 'active'
            user.save(update_fields=['status'])
            clear_otp_from_session(request)
            login(request, user)
            messages.success(request, 'Email verified successfully! Welcome to E-Society.')
            return _redirect_by_role(user)

        messages.error(request, error_msg)
        # If session was cleared (expired / locked), send back to login
        if not get_otp_from_session(request):
            return redirect('login')

    return render(request, 'core/verify_otp.html', {'email': user.email})


@never_cache
@require_http_methods(['POST'])
def resendOtpView(request):
    otp_data = get_otp_from_session(request)
    if not otp_data:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    try:
        user = User.objects.get(pk=otp_data['user_id'])
    except User.DoesNotExist:
        clear_otp_from_session(request)
        return redirect('login')

    otp_code = generate_otp()
    store_otp_in_session(request, user.pk, otp_code)
    _send_otp_email(user, otp_code)
    messages.success(request, 'A new OTP has been sent to your email.')
    return redirect('verify_otp')

def book_demo(request):
    if request.method == 'POST':
        form = DemoBookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Demo booked! We will contact you soon.')
            return redirect('home')
        else:
            # Pass form WITH errors back to home template
            return render(request, 'home.html', {'form': form})
    return redirect('home')