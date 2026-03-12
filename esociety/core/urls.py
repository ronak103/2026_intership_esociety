from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('signup/',views.userSignupView,name='signup'),
    path('login/',views.userLoginview,name='login'),
    path('logout/',views.LogoutView,name='logout'),
    path('verify-otp/',views.verifyOtpView,name='verify_otp'),  
    path('resend-otp/', views.resendOtpView,  name='resend_otp'),
]