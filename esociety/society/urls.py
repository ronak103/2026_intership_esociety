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
   
    path("resident/visitor-approval/",views.visitor_approvals,name="resident_visitor_approval"),
    path("resident/visitor/<int:visitor_id>/decision/<str:decision>/",views.visitor_decision,name="visitor_decision"),
    path("resident/payments/", views.resident_payments,name="resident_payments"),
    path("resident/notifications/",views.resident_notifications, name="resident_notifications"),
    path("resident/notifications/mark-read/", views.ResidentMarkAllReadView, name="resident_mark_all_read"),
    path("resident/settings/",views.resident_settings,name="resident_settings"),
    path("resident/changepassword/",views.resident_change_password,name="resident_change_password"),
    path("resident/poll/<int:poll_id>/vote/<str:vote>/", views.resident_poll_vote, name="poll_vote"),
    path("guard/log-visitor/",views.guard_log_visitor,name="guard_log_visitor"),
    path("guard/visitor/<int:visitor_id>/entry/<str:action>/", views.guard_update_entry,name="guard_update_entry"),

    path("admin/residents/",views.AdminResidentsView,name="admin_residents"),
    path("admin/residents/add/",views.AdminAddResidentView,name="admin_add_resident"),
    path("admin/residents/<int:resident_id>/toggle/",views.AdminToggleResidentView, name="admin_toggle_resident"),


    # Complaints
    path("admin/complaints/", views.AdminComplaintsView, name="admin_complaints"),
    path("admin/complaints/update/",views.AdminUpdateComplaintView, name="admin_update_complaint"),

    path("admin/visitor-logs/",views.AdminVisitorLogsView,name="admin_visitor_logs"),

    # Finance
    path("admin/finance/", views.AdminFinanceView,name="admin_finance"),
    path("admin/finance/payment/add/", views.AdminAddPaymentView,name="admin_add_payment"),
    path("admin/finance/payment/<int:payment_id>/mark-paid/", views.AdminMarkPaidView, name="admin_mark_paid"),
    path("admin/finance/booking/<int:booking_id>/confirm/", views.AdminConfirmBookingView, name="admin_confirm_booking"),
    path("admin/finance/booking/<int:booking_id>/cancel/", views.AdminCancelBookingView,  name="admin_cancel_booking"),
    path("admin/maintenance/", views.AdminMaintenanceView, name="admin_maintenance"),
    path("admin/maintenance/config/save/", views.AdminSaveMaintenanceConfigView, name="admin_save_maintenance_config"),
    path("admin/maintenance/generate/",  views.AdminGenerateDuesView, name="admin_generate_dues"),
    path("admin/maintenance/due/<int:due_id>/paid/", views.AdminMarkDuePaidView,name="admin_mark_due_paid"),
    path("admin/maintenance/due/<int:due_id>/waive/", views.AdminWaiveDueView,  name="admin_waive_due"),
    path("admin/maintenance/due/<int:due_id>/delete/", views.AdminDeleteDueView,name="admin_delete_due"),
    path("admin/maintenance/mark-overdue/",  views.AdminMarkOverdueView,name="admin_mark_overdue"),
    path("admin/maintenance/export/",  views.AdminExportDuesView,name="admin_export_dues"),

    # Community
    path("admin/community/", views.AdminCommunityView, name="admin_community"),
    path("admin/community/notice/add/", views.AdminAddNoticeView, name="admin_add_notice"),
    path("admin/community/notice/<int:notice_id>/delete/", views.AdminDeleteNoticeView, name="admin_delete_notice"),
    path("admin/community/poll/add/", views.AdminAddPollView,name="admin_add_poll"),
    path("admin/community/poll/<int:poll_id>/close/", views.AdminClosePollView, name="admin_close_poll"),
    path("admin/community/poll/<int:poll_id>/delete/",views.AdminDeletePollView,name="admin_delete_poll"),

    # Settings
    path("admin/settings/",views.AdminSettingsView,name="admin_settings"),
    path("admin/settings/save/",views.AdminSaveSettingsView,name="admin_save_settings"),
    path("admin/settings/password/",views.AdminChangePasswordView,name="admin_change_password"),
    path("admin/settings/facility/add/",views.AdminAddFacilityView,name="admin_add_facility"),
    path("admin/settings/facility/<int:facility_id>/toggle/", views.AdminToggleFacilityView, name="admin_toggle_facility"),
    path("admin/export-all/",views.AdminExportAllView,name="admin_export_all"),
    path("admin/notifications/mark-read/", views.AdminMarkAllReadView, name="admin_mark_all_read"),

    # guard urls
    path("guard/notifications/",views.guard_notifications,name="guard_notifications"),
    path("guard/notifications/mark-read/",views.guard_mark_all_read,name="guard_mark_all_read"),
    path("guard/settings/",views.guard_settings,name="guard_settings"),
    path("guard/settings/password/",views.guard_change_password,name="guard_change_password"),


    
]

