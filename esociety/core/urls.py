from django.contrib import admin # type: ignore
import django.urls # type: ignore
from . import views

urlpatterns = [
    # ── Public auth ──────────────────────────────────────
    django.urls.path('signup/',                        views.userSignupView,      name='signup'),
    django.urls.path('login/',                         views.userLoginview,       name='login'),
    django.urls.path('logout/',                        views.LogoutView,          name='logout'),
    django.urls.path('verify-otp/',                    views.verifyOtpView,       name='verify_otp'),
    django.urls.path('resend-otp/',                    views.resendOtpView,       name='resend_otp'),

    # ── Forgot password ──────────────────────────────────
    django.urls.path('forgot-password/',               views.forgotPasswordView,  name='forgot_password'),
    django.urls.path('forgot-password/verify-otp/',    views.forgotVerifyOtpView, name='forgot_verify_otp'),
    django.urls.path('forgot-password/resend-otp/',    views.forgotResendOtpView, name='forgot_resend_otp'),
    django.urls.path('forgot-password/reset/',         views.resetPasswordView,   name='reset_password'),

    # ── Admin: user approval (staff_member_required) ─────
    django.urls.path('admin/pending-users/',           views.pendingUsersView,    name='pending_users'),
    django.urls.path('admin/approve/<int:user_id>/',   views.approveUserView,     name='approve_user'),
    django.urls.path('admin/reject/<int:user_id>/',    views.rejectUserView,      name='reject_user'),

    # ── Admin: create security guard (staff_member_required) ──
    django.urls.path('admin/create-staff/',            views.createStaffView,     name='create_staff'),
]