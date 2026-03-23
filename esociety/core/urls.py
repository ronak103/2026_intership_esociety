from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # ── Public auth ──────────────────────────────────────
    path('signup/',                        views.userSignupView,      name='signup'),
    path('login/',                         views.userLoginview,       name='login'),
    path('logout/',                        views.LogoutView,          name='logout'),
    path('verify-otp/',                    views.verifyOtpView,       name='verify_otp'),
    path('resend-otp/',                    views.resendOtpView,       name='resend_otp'),

    # ── Forgot password ──────────────────────────────────
    path('forgot-password/',               views.forgotPasswordView,  name='forgot_password'),
    path('forgot-password/verify-otp/',    views.forgotVerifyOtpView, name='forgot_verify_otp'),
    path('forgot-password/resend-otp/',    views.forgotResendOtpView, name='forgot_resend_otp'),
    path('forgot-password/reset/',         views.resetPasswordView,   name='reset_password'),

    # ── Admin: user approval (staff_member_required) ─────
    path('admin/pending-users/',           views.pendingUsersView,    name='pending_users'),
    path('admin/approve/<int:user_id>/',   views.approveUserView,     name='approve_user'),
    path('admin/reject/<int:user_id>/',    views.rejectUserView,      name='reject_user'),

    # ── Admin: create security guard (staff_member_required) ──
    path('admin/create-staff/',            views.createStaffView,     name='create_staff'),
]