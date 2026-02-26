from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .decorators import role_required
# Create your views here.
# @login_required(login_url="login") #check in core.urls.py login name should exist..
@role_required(allowed_roles=["Admin"]) #check in core.urls.py login name should exist..
def AdminDashboardView(request):
    return render(request,"society/Admin/Admin_dashboard.html")

# @login_required(login_url="login")
@role_required(allowed_roles=["Resident"]) 
def ResidentDashboardView(request):
    return render(request,"society/Resident/Resident_dashboard.html")

# @login_required(login_url="login")
@role_required(allowed_roles=["Securityguard"])
def SecurityDashboardView(request):
    return render(request,"society/Securityguard/Security_dashboard.html")

