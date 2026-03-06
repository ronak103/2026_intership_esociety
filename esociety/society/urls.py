from django.urls import path
from . import views

urlpatterns = [
    path("admin/",views.AdminDashboardView,name="admin_dashboard"),
    path("resident/",views.ResidentDashboardView,name="resident_dashboard"),
    path("security/",views.SecurityDashboardView,name="security_dashboard"),
    path("visitor_pass/",views.visitor_pass,name="visitor_pass"),
    path("complaints/",views.complaints,name="complaints"),
    path("facility_booking/",views.facility_booking,name="facility_booking"),
    path("community_notice/",views.community_notice,name="community_notice"),
]