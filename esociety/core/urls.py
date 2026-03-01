from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('signup/',views.authView,name='signup'),
    path('login/',views.authView,name='login'),
    path('logout/',views.LogoutView,name='logout')
   
]