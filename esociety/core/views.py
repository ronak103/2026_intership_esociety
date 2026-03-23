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

from .forms import UserSignupForm, UserLoginForm, DemoBookingForm, ForgotPasswordForm, ResetPasswordForm, StaffCreateForm
from .models import User, DemoBooking
from society.decorators import role_required

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────
OTP_EXPIRY_SECONDS = 5 * 60   # 5 minutes
OTP_MAX_ATTEMPTS   = 5


def home(request):
    form = DemoBookingForm()
    return render(request, 'home.html', {'form': form})


# ════════════════════════════════════════════════════════
#  SESSION-BASED OTP FUNCTIONS
# ════════════════════════════════════════════════════════

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def store_otp_in_session(request, user_id, otp_code):
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

    otp_data['is_used'] = True
    request.session['otp'] = otp_data
    request.session.modified = True
    return True, None


# ════════════════════════════════════════════════════════
#  EMAIL HELPERS
# ════════════════════════════════════════════════════════

def _send_otp_email(user, otp_code):
    def _send():
        try:
            html = render_to_string('core/otp_email.html', {
                'first_name': user.first_name or user.email,
                'otp_code':   otp_code,
                'expiry_min': OTP_EXPIRY_SECONDS // 60,
            })
            msg = EmailMultiAlternatives(
                subject='Your GateNova Login OTP',
                body=otp_code,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email],
            )
            msg.attach_alternative(html, 'text/html')
            msg.send()
        except Exception as exc:
            logger.exception('OTP email failed for %s: %s', user.email, exc)
    threading.Thread(target=_send, daemon=True).start()


def _send_forgot_otp_email(user, otp_code):
    def _send():
        try:
            html = render_to_string('core/otp_email.html', {
                'first_name': user.first_name or user.email,
                'otp_code':   otp_code,
                'expiry_min': OTP_EXPIRY_SECONDS // 60,
            })
            msg = EmailMultiAlternatives(
                subject='GateNova — Reset Your Password',
                body=otp_code,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email],
            )
            msg.attach_alternative(html, 'text/html')
            msg.send()
        except Exception as exc:
            logger.exception('Forgot OTP email failed for %s: %s', user.email, exc)
    threading.Thread(target=_send, daemon=True).start()


def _send_welcome_email(user):
    def _send():
        try:
            html = render_to_string('core/welcome_email.html', {
                'first_name': user.first_name or user.email,
            })
            msg = EmailMultiAlternatives(
                subject='Welcome to GateNova',
                body='Welcome to GateNova',
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


def _send_approval_result_email(user, approved: bool):
    """Notifies the user whether their account was approved or rejected."""
    def _send():
        try:
            if approved:
                subject = 'GateNova — Your account has been approved!'
                body    = (
                    f'Hi {user.first_name},\n\n'
                    'Great news! Your GateNova account has been approved by the admin.\n'
                    'You can now log in and access your dashboard.\n\n'
                    '— The GateNova Team'
                )
            else:
                subject = 'GateNova — Account not approved'
                body    = (
                    f'Hi {user.first_name},\n\n'
                    'Unfortunately your GateNova account was not approved at this time.\n'
                    'Please contact your society admin for more information.\n\n'
                    '— The GateNova Team'
                )
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email],
            )
            msg.send()
        except Exception as exc:
            logger.exception('Approval result email failed for %s: %s', user.email, exc)
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
#  AUTH VIEWS
# ════════════════════════════════════════════════════════

@never_cache
def userSignupView(request):
    signup_form = UserSignupForm(request.POST or None)
    login_form  = UserLoginForm()
    active_form = 'signup'

    if request.method == 'POST' and signup_form.is_valid():
        user = signup_form.save()
        _send_welcome_email(user)
        messages.success(
            request,
            'Account created successfully! Please wait for admin approval before logging in.'
        )
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

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Account does not exist.')
            return _auth_render(request, login_form, signup_form, active_form)

        if not user.check_password(password):
            messages.error(request, 'Invalid email or password.')
            return _auth_render(request, login_form, signup_form, active_form)

        if user.status == 'deleted':
            messages.error(request, 'Account does not exist.')
            return _auth_render(request, login_form, signup_form, active_form)

        if user.status == 'blocked':
            messages.error(request, 'Your account has been blocked. Please contact support.')
            return _auth_render(request, login_form, signup_form, active_form)

        # ── Admin / staff: bypass all status checks ──────────────────────────
        if user.is_staff or user.is_admin:
            # Already active — log in directly, no OTP needed
            if user.status == 'active':
                login(request, user)
                return _redirect_by_role(user)
            # Inactive (first time) — send OTP to verify email
            otp_code = generate_otp()
            store_otp_in_session(request, user.pk, otp_code)
            _send_otp_email(user, otp_code)
            messages.info(
                request,
                f'A 6-digit OTP has been sent to {user.email}. It expires in {OTP_EXPIRY_SECONDS // 60} minutes.'
            )
            return redirect('verify_otp')

        # ── Pending: signed up but not yet approved by admin ─────────────────
        if user.status == 'pending':
            messages.warning(
                request,
                'Your account is pending admin approval. You will receive an email once approved.'
            )
            return _auth_render(request, login_form, signup_form, active_form)

        # ── Active: go straight to dashboard ─────────────────────────────────
        if user.status == 'active':
            login(request, user)
            return _redirect_by_role(user)

        # ── Inactive: first-time login — send OTP for email verification ──────
        otp_code = generate_otp()
        store_otp_in_session(request, user.pk, otp_code)
        _send_otp_email(user, otp_code)
        messages.info(
            request,
            f'A 6-digit OTP has been sent to {user.email}. It expires in {OTP_EXPIRY_SECONDS // 60} minutes.'
        )
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
        if request.POST.get('otp'):
            submitted = request.POST.get('otp', '').strip()
        else:
            digits    = [request.POST.get(f'otp{i}', '').strip() for i in range(1, 7)]
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
            messages.success(request, 'Email verified successfully! Welcome to GateNova.')
            return _redirect_by_role(user)

        messages.error(request, error_msg)
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
            return render(request, 'home.html', {'form': form})
    return redirect('home')


# ════════════════════════════════════════════════════════
#  FORGOT PASSWORD VIEWS
# ════════════════════════════════════════════════════════

@never_cache
def forgotPasswordView(request):
    """Step 1 — User enters email. OTP sent if account exists."""
    form = ForgotPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        user  = User.objects.get(email=email)

        otp_code = generate_otp()
        request.session['fp_otp'] = {
            'user_id':    user.pk,
            'code':       otp_code,
            'created_at': timezone.now().isoformat(),
            'attempts':   0,
            'is_used':    False,
        }
        request.session.modified = True

        _send_forgot_otp_email(user, otp_code)
        messages.success(request, f'A 6-digit OTP has been sent to {email}.')
        return redirect('forgot_verify_otp')

    return render(request, 'core/forgot_password.html', {'form': form})


@never_cache
def forgotVerifyOtpView(request):
    """Step 2 — User enters the OTP received in email."""
    fp_otp = request.session.get('fp_otp')

    if not fp_otp:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')

    try:
        user = User.objects.get(pk=fp_otp['user_id'])
    except User.DoesNotExist:
        request.session.pop('fp_otp', None)
        return redirect('forgot_password')

    if request.method == 'POST':
        digits    = [request.POST.get(f'otp{i}', '').strip() for i in range(1, 7)]
        submitted = ''.join(digits)

        if len(submitted) != 6 or not submitted.isdigit():
            messages.error(request, 'Please enter all 6 digits.')
            return render(request, 'core/forgot_verify_otp.html', {'email': user.email})

        created_at = timezone.datetime.fromisoformat(fp_otp['created_at'])
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at)
        if timezone.now() > created_at + timezone.timedelta(seconds=OTP_EXPIRY_SECONDS):
            request.session.pop('fp_otp', None)
            messages.error(request, 'OTP has expired. Please try again.')
            return redirect('forgot_password')

        if fp_otp.get('attempts', 0) >= OTP_MAX_ATTEMPTS:
            request.session.pop('fp_otp', None)
            messages.error(request, 'Too many incorrect attempts. Please try again.')
            return redirect('forgot_password')

        if fp_otp['code'] != submitted:
            fp_otp['attempts'] += 1
            request.session['fp_otp'] = fp_otp
            request.session.modified  = True
            remaining = OTP_MAX_ATTEMPTS - fp_otp['attempts']
            messages.error(request, f'Incorrect OTP. {remaining} attempt(s) remaining.')
            return render(request, 'core/forgot_verify_otp.html', {'email': user.email})

        fp_otp['is_verified'] = True
        request.session['fp_otp'] = fp_otp
        request.session.modified   = True
        return redirect('reset_password')

    return render(request, 'core/forgot_verify_otp.html', {'email': user.email})


@never_cache
@require_http_methods(['POST'])
def forgotResendOtpView(request):
    """Resend OTP during forgot password flow."""
    fp_otp = request.session.get('fp_otp')
    if not fp_otp:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')

    try:
        user = User.objects.get(pk=fp_otp['user_id'])
    except User.DoesNotExist:
        request.session.pop('fp_otp', None)
        return redirect('forgot_password')

    otp_code = generate_otp()
    request.session['fp_otp'] = {
        'user_id':    user.pk,
        'code':       otp_code,
        'created_at': timezone.now().isoformat(),
        'attempts':   0,
        'is_used':    False,
    }
    request.session.modified = True
    _send_forgot_otp_email(user, otp_code)
    messages.success(request, 'A new OTP has been sent to your email.')
    return redirect('forgot_verify_otp')


@never_cache
def resetPasswordView(request):
    """Step 3 — User sets a new password."""
    fp_otp = request.session.get('fp_otp')

    if not fp_otp or not fp_otp.get('is_verified'):
        messages.error(request, 'Unauthorized. Please complete OTP verification first.')
        return redirect('forgot_password')

    try:
        user = User.objects.get(pk=fp_otp['user_id'])
    except User.DoesNotExist:
        request.session.pop('fp_otp', None)
        return redirect('forgot_password')

    form = ResetPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['password1'])
        user.save()
        request.session.pop('fp_otp', None)
        messages.success(request, 'Password reset successful! Please log in with your new password.')
        return redirect('login')

    return render(request, 'core/reset_password.html', {'form': form})


# ════════════════════════════════════════════════════════
#  ADMIN — PENDING USER APPROVAL VIEWS
# ════════════════════════════════════════════════════════

@role_required(allowed_roles=['Admin'])
def pendingUsersView(request):
    """Admin sees a list of all users waiting for approval."""
    pending = User.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'society/Admin/pending_users.html', {
        'pending_users':    pending,
        'total_residents':  User.objects.filter(role='Resident').count(),
        'active_residents': User.objects.filter(role='Resident', status='active').count(),
    })


@role_required(allowed_roles=['Admin'])
def approveUserView(request, user_id):
    """Admin approves a pending user → status becomes active."""
    try:
        user = User.objects.get(pk=user_id, status='pending')
    except User.DoesNotExist:
        messages.error(request, 'User not found or already processed.')
        return redirect('pending_users')

    user.status = 'active'
    user.save(update_fields=['status'])
    _send_approval_result_email(user, approved=True)
    messages.success(request, f'{user.email} has been approved.')
    return redirect('pending_users')


@role_required(allowed_roles=['Admin'])
def rejectUserView(request, user_id):
    """Admin rejects a pending user → status becomes blocked."""
    try:
        user = User.objects.get(pk=user_id, status='pending')
    except User.DoesNotExist:
        messages.error(request, 'User not found or already processed.')
        return redirect('pending_users')

    user.status = 'blocked'
    user.save(update_fields=['status'])
    _send_approval_result_email(user, approved=False)
    messages.success(request, f'{user.email} has been rejected.')
    return redirect('pending_users')


# ════════════════════════════════════════════════════════
#  ADMIN — CREATE SECURITY GUARD ACCOUNT
# ════════════════════════════════════════════════════════

@role_required(allowed_roles=['Admin'])
def createStaffView(request):
    """Admin creates a Security Guard account directly.
    Guards never go through the public signup form."""
    form = StaffCreateForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, f'Security Guard account created for {user.email}.')
        return redirect('admin_dashboard')

    return render(request, 'society/Admin/create_staff.html', {'form': form})