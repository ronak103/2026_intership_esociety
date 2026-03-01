from django.urls import path
from . import views

urlpatterns = [
    path("admin/",views.AdminDashboardView,name="admin_dashboard"),
    path("resident/",views.ResidentDashboardView,name="resident_dashboard"),
    path("security/",views.SecurityDashboardView,name="security_dashboard")
    
]