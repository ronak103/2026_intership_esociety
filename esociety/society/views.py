from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .forms import ComplaintForm
from .models import Complaint
from core.models import User

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

@role_required(allowed_roles=["Resident"])
def visitor_pass(request):
    return render(request,"society/Resident/visitor_pass.html")


def complaints(request):

    # If request.user is already a User object
    if isinstance(request.user, User):
        user = request.user
    else:
        # If request.user is email stored in session
        user = User.objects.get(email=request.user)

    if request.method == "POST":

        form = ComplaintForm(request.POST)

        if form.is_valid():

            complaint = form.save(commit=False)

            complaint.resident = user

            complaint.save()

            return redirect("complaints")

    else:
        form = ComplaintForm()

    complaints = Complaint.objects.filter(
        resident=user
    ).order_by("-created_at")

    context = {
        "form": form,
        "complaints": complaints
    }

    return render(
        request,
        "society/Resident/Resident_complaints.html",
        context
    )

@role_required(allowed_roles=["Resident"])
def facility_booking(request):
    return render(request, "society/Resident/booking.html")

@role_required(allowed_roles=["Resident"])
def community_notice(request):
    return render(request, "society/Resident/Resident_community.html")