from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# Create your views here.
@login_required(login_url="login") #check in core.urls.py login name should exist..
def AdminDashboardView(request):
    return render(request,"society/Admin_dashboard.html")

@login_required(login_url="login")
def ResidentDashboardView(request):
    return render(request,"society/Resident_dashboard.html")

@login_required(login_url="login")
def SecurityDashboardView(request):
    return render(request,"society/Security_dashboard.html")

