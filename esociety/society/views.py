from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
import csv
from django.http import HttpResponse
from datetime import date
import calendar
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .forms import (
    ComplaintForm,
    VisitorForm,
    GuardVisitorForm,
    AdminAddResidentForm,
    AdminComplaintUpdateForm,
    AdminPaymentForm,
    AdminNoticeForm,
    AdminPollForm,
    AdminFacilityForm,
    AdminChangePasswordForm,
    AdminSocietySettingsForm,
    MaintenanceConfigForm, GenerateDuesForm
)
from .models import (
    Complaint,
    Visitor,
    Notification,
    Payment,
    Notice,
    Poll,
    PollVote,
    Facility,
    FacilityBooking,
    MaintenanceDue, MaintenanceConfig
)
from core.models import User


# ── Shared helper — pending count injected into every admin context ──────────
def _pending_count():
    return User.objects.filter(status='pending').count()


# ================================================================
# ADMIN — DASHBOARD
# ================================================================
@role_required(allowed_roles=["Admin"])
def AdminDashboardView(request):
    today = date.today()

    total_residents    = User.objects.filter(role="Resident").count()
    security_guards    = User.objects.filter(role="Securityguard").count()
    pending_complaints  = Complaint.objects.filter(status="pending").count()
    resolved_complaints = Complaint.objects.filter(status="resolved").count()

    total_collected   = Payment.objects.filter(payment_status="completed").aggregate(t=Sum("amount"))["t"] or 0
    pending_payments  = Payment.objects.filter(payment_status="pending").count()
    pending_dues      = Payment.objects.filter(payment_status="pending").aggregate(t=Sum("amount"))["t"] or 0
    maintenance_collected = Payment.objects.filter(payment_status="completed", payment_type="maintenance").aggregate(t=Sum("amount"))["t"] or 0
    facility_collected    = Payment.objects.filter(payment_status="completed", payment_type="facility_booking").aggregate(t=Sum("amount"))["t"] or 0

    combined = maintenance_collected + facility_collected + pending_dues
    maintenance_pct = int((maintenance_collected / combined) * 100) if combined else 0
    facility_pct    = int((facility_collected    / combined) * 100) if combined else 0
    dues_pct        = int((pending_dues          / combined) * 100) if combined else 0

    today_visitors  = Visitor.objects.filter(expected_date=today).count()
    inside_visitors = Visitor.objects.filter(entry_status="inside").count()
    total_notices   = Notice.objects.count()
    total_polls     = Poll.objects.filter(status="active").count()

    recent_complaints = Complaint.objects.select_related("resident").order_by("-created_at")[:8]
    recent_payments   = Payment.objects.select_related("resident").order_by("-created_at")[:6]
    recent_notices    = Notice.objects.order_by("-created_at")[:4]

    visitor_status_today = [
        {"label": "Total Visitors",      "count": today_visitors,  "badge": "badge-info"},
        {"label": "Currently Inside",    "count": inside_visitors, "badge": "badge-success"},
        {"label": "Pre-Approved Passes", "count": Visitor.objects.filter(expected_date=today, registered_by="resident").count(), "badge": "badge-cyan"},
        {"label": "Guard Logged",        "count": Visitor.objects.filter(expected_date=today, registered_by="guard").count(),    "badge": "badge-warning"},
        {"label": "Denied Entry",        "count": Visitor.objects.filter(expected_date=today, entry_status="denied").count(),    "badge": "badge-danger"},
    ]

    context = {
        "total_residents":       total_residents,
        "security_guards":       security_guards,
        "pending_complaints":    pending_complaints,
        "resolved_complaints":   resolved_complaints,
        "total_collected":       total_collected,
        "pending_payments":      pending_payments,
        "today_visitors":        today_visitors,
        "inside_visitors":       inside_visitors,
        "total_notices":         total_notices,
        "total_polls":           total_polls,
        "maintenance_collected": maintenance_collected,
        "facility_collected":    facility_collected,
        "pending_dues":          pending_dues,
        "maintenance_pct":       maintenance_pct,
        "facility_pct":          facility_pct,
        "dues_pct":              dues_pct,
        "recent_complaints":     recent_complaints,
        "recent_payments":       recent_payments,
        "recent_notices":        recent_notices,
        "visitor_status_today":  visitor_status_today,
        "pending_count":         _pending_count(),   # ← sidebar badge
        "active_residents":      User.objects.filter(role="Resident", status="active").count(),  # ← pending_users page needs this
    }
    return render(request, "society/Admin/Admin_dashboard.html", context)


# ================================================================
# ADMIN — RESIDENTS
# ================================================================
@role_required(allowed_roles=["Admin"])
def AdminResidentsView(request):
    search_query  = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "all")

    # ── Only show approved residents — pending users belong in the approval queue
    residents = User.objects.filter(
        role="Resident",
        status__in=["active", "inactive", "blocked"]
    ).order_by("first_name")

    if search_query:
        residents = residents.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)  |
            Q(email__icontains=search_query)      |
            Q(unit_number__icontains=search_query)
        )
    if status_filter == "active":
        residents = residents.filter(is_active=True)
    elif status_filter == "inactive":
        residents = residents.filter(is_active=False)

    residents = residents.annotate(
        complaint_count=Count("complaints", distinct=True),
        pending_payment_count=Count(
            "payments",
            filter=Q(payments__payment_status="pending"),
            distinct=True,
        ),
    )

    # CSV export
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="residents.csv"'
        writer = csv.writer(response)
        writer.writerow(["Name", "Email", "Unit", "Mobile", "Active", "Joined", "Complaints", "Pending Payments"])
        for r in residents:
            writer.writerow([
                f"{r.first_name} {r.last_name}",
                r.email,
                getattr(r, "unit_number", "—"),
                getattr(r, "mobile_number", "—"),
                "Yes" if r.is_active else "No",
                r.created_at.strftime("%d %b %Y") if r.created_at else "—",
                r.complaint_count,
                r.pending_payment_count,
            ])
        return response

    paginator = Paginator(residents, 20)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    add_form = AdminAddResidentForm()

    context = {
        "residents":        page_obj,
        "page_obj":         page_obj,
        "is_paginated":     page_obj.has_other_pages(),
        "search_query":     search_query,
        "status_filter":    status_filter,
        "add_form":         add_form,
        "total_residents":  User.objects.filter(role="Resident").count(),
        "active_residents": User.objects.filter(role="Resident", is_active=True).count(),
        "occupied_units":   User.objects.filter(role="Resident", is_active=True)
                                .exclude(unit_number="").exclude(unit_number__isnull=True).count(),
        "security_guards":  User.objects.filter(role="Securityguard").count(),
        "pending_count":    _pending_count(),   # ← sidebar badge
    }
    return render(request, "society/Admin/Admin_Residents.html", context)


@role_required(allowed_roles=["Admin"])
def AdminAddResidentView(request):
    if request.method == "POST":
        form = AdminAddResidentForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if User.objects.filter(email=cd["email"]).exists():
                messages.error(request, "A user with this email already exists.")
            else:
                user = User.objects.create_user(
                    email=cd["email"],
                    password=cd["password"],
                    first_name=cd["first_name"],
                    last_name=cd["last_name"],
                    role="Resident",
                )
                # ── Admin-created residents are active immediately ────────────
                # They bypass the public signup approval flow entirely.
                user.status       = "active"
                user.unit_number  = cd.get("unit_number", "")
                user.mobile_number = cd.get("mobile_number", "")
                user.save()
                messages.success(request, f"Resident '{cd['first_name']} {cd['last_name']}' added successfully.")
        else:
            residents = User.objects.filter(
                role="Resident",
                status__in=["active", "inactive", "blocked"]
            ).order_by("first_name").annotate(
                complaint_count=Count("complaints", distinct=True),
                pending_payment_count=Count("payments", filter=Q(payments__payment_status="pending"), distinct=True),
            )
            paginator = Paginator(residents, 20)
            page_obj  = paginator.get_page(1)
            context = {
                "residents":        page_obj,
                "page_obj":         page_obj,
                "is_paginated":     page_obj.has_other_pages(),
                "search_query":     "",
                "status_filter":    "all",
                "add_form":         form,
                "show_add_modal":   True,
                "total_residents":  User.objects.filter(role="Resident").count(),
                "active_residents": User.objects.filter(role="Resident", is_active=True).count(),
                "occupied_units":   User.objects.filter(role="Resident", is_active=True)
                                        .exclude(unit_number="").exclude(unit_number__isnull=True).count(),
                "security_guards":  User.objects.filter(role="Securityguard").count(),
                "pending_count":    _pending_count(),   # ← sidebar badge
            }
            return render(request, "society/Admin/Admin_Residents.html", context)

    return redirect("admin_residents")


@role_required(allowed_roles=["Admin"])
def AdminToggleResidentView(request, resident_id):
    resident = get_object_or_404(User, id=resident_id, role="Resident")
    resident.is_active = not resident.is_active
    resident.save()
    status = "activated" if resident.is_active else "deactivated"
    messages.success(request, f"'{resident.first_name}' has been {status}.")
    return redirect("admin_residents")


# ================================================================
# ADMIN — COMPLAINTS
# ================================================================
@role_required(allowed_roles=["Admin"])
def AdminComplaintsView(request):
    search_query    = request.GET.get("q",        "").strip()
    status_filter   = request.GET.get("status",   "all")
    priority_filter = request.GET.get("priority", "all")

    complaints_qs = Complaint.objects.select_related("resident").order_by("-created_at")

    if search_query:
        complaints_qs = complaints_qs.filter(
            Q(complaint_type__icontains=search_query)         |
            Q(resident__first_name__icontains=search_query)   |
            Q(resident__last_name__icontains=search_query)
        )
    if status_filter != "all":
        complaints_qs = complaints_qs.filter(status=status_filter)
    if priority_filter != "all":
        complaints_qs = complaints_qs.filter(priority=priority_filter)

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="complaints.csv"'
        writer = csv.writer(response)
        writer.writerow(["Resident", "Unit", "Type", "Description", "Priority", "Status", "Assigned Staff", "Date"])
        for c in complaints_qs:
            writer.writerow([
                f"{c.resident.first_name} {c.resident.last_name}",
                getattr(c.resident, "unit_number", "—"),
                c.complaint_type,
                c.description,
                c.priority,
                c.status,
                c.assigned_staff or "—",
                c.created_at.strftime("%d %b %Y"),
            ])
        return response

    paginator = Paginator(complaints_qs, 20)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    update_form = AdminComplaintUpdateForm()

    context = {
        "complaints":        page_obj,
        "page_obj":          page_obj,
        "is_paginated":      page_obj.has_other_pages(),
        "search_query":      search_query,
        "status_filter":     status_filter,
        "priority_filter":   priority_filter,
        "update_form":       update_form,
        "pending_count":     Complaint.objects.filter(status="pending").count(),
        "in_progress_count": Complaint.objects.filter(status="in_progress").count(),
        "resolved_count":    Complaint.objects.filter(status="resolved").count(),
        "urgent_count":      Complaint.objects.filter(priority="urgent").count(),
        "pending_count":     _pending_count(),   # ← sidebar badge (overrides complaint pending_count — rename below)
    }
    # Fix: separate variable names to avoid collision
    context["complaint_pending_count"]  = Complaint.objects.filter(status="pending").count()
    context["pending_count"]            = _pending_count()
    return render(request, "society/Admin/Admin_complaints.html", context)


@role_required(allowed_roles=["Admin"])
def AdminUpdateComplaintView(request):
    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")
        complaint    = get_object_or_404(Complaint, id=complaint_id)

        form = AdminComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.status == "resolved" and not complaint.resolved_at:
                updated.resolved_at = timezone.now()
            updated.save()
            messages.success(request, f"Complaint updated to '{updated.get_status_display()}'.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return redirect("admin_complaints")


# ================================================================
# ADMIN — FINANCE
# ================================================================
@role_required(allowed_roles=["Admin"])
def AdminFinanceView(request):
    active_tab    = request.GET.get("tab",    "payments")
    search_query  = request.GET.get("q",      "").strip()
    type_filter   = request.GET.get("type",   "all")
    status_filter = request.GET.get("status", "all")

    total_collected   = Payment.objects.filter(payment_status="completed").aggregate(t=Sum("amount"))["t"] or 0
    total_pending     = Payment.objects.filter(payment_status="pending").aggregate(t=Sum("amount"))["t"] or 0
    completed_count   = Payment.objects.filter(payment_status="completed").count()
    payment_pending_count = Payment.objects.filter(payment_status="pending").count()
    maintenance_total = Payment.objects.filter(payment_status="completed", payment_type="maintenance").aggregate(t=Sum("amount"))["t"] or 0
    facility_total    = Payment.objects.filter(payment_status="completed", payment_type="facility_booking").aggregate(t=Sum("amount"))["t"] or 0

    if request.GET.get("export") == "csv":
        payments_all = Payment.objects.select_related("resident").order_by("-created_at")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="payments.csv"'
        writer = csv.writer(response)
        writer.writerow(["Resident", "Unit", "Type", "Amount", "Transaction ID", "Date", "Status"])
        for p in payments_all:
            writer.writerow([
                f"{p.resident.first_name} {p.resident.last_name}",
                getattr(p.resident, "unit_number", "—"),
                p.get_payment_type_display(),
                p.amount,
                p.transaction_id or "—",
                p.payment_date,
                p.payment_status,
            ])
        return response

    payment_form = AdminPaymentForm()

    context = {
        "active_tab":            active_tab,
        "total_collected":       total_collected,
        "total_pending":         total_pending,
        "completed_count":       completed_count,
        "payment_pending_count": payment_pending_count,  # renamed to avoid clash
        "maintenance_total":     maintenance_total,
        "facility_total":        facility_total,
        "payment_form":          payment_form,
        "search_query":          search_query,
        "type_filter":           type_filter,
        "status_filter":         status_filter,
        "pending_count":         _pending_count(),   # ← sidebar badge
    }

    if active_tab == "payments":
        payments_qs = Payment.objects.select_related("resident").order_by("-created_at")
        if search_query:
            payments_qs = payments_qs.filter(
                Q(resident__first_name__icontains=search_query) |
                Q(resident__last_name__icontains=search_query)  |
                Q(transaction_id__icontains=search_query)
            )
        if type_filter != "all":
            payments_qs = payments_qs.filter(payment_type=type_filter)
        if status_filter != "all":
            payments_qs = payments_qs.filter(payment_status=status_filter)

        paginator = Paginator(payments_qs, 20)
        page_obj  = paginator.get_page(request.GET.get("page", 1))
        context.update({"payments": page_obj, "page_obj": page_obj, "is_paginated": page_obj.has_other_pages()})

    elif active_tab == "bookings":
        context["bookings"] = FacilityBooking.objects.select_related("facility", "booked_by").order_by("-created_at")

    elif active_tab == "defaulters":
        defaulter_ids = (
            Payment.objects.filter(payment_status="pending")
            .values_list("resident_id", flat=True)
            .distinct()
        )
        defaulters = []
        for uid in defaulter_ids:
            try:
                user = User.objects.get(id=uid, role="Resident")
                pending_pmts  = Payment.objects.filter(resident=user, payment_status="pending")
                total_due     = pending_pmts.aggregate(t=Sum("amount"))["t"] or 0
                last_pay      = Payment.objects.filter(resident=user, payment_status="completed").order_by("-payment_date").first()
                user.pending_count = pending_pmts.count()
                user.total_due     = total_due
                user.last_payment  = last_pay.payment_date if last_pay else None
                defaulters.append(user)
            except User.DoesNotExist:
                pass
        defaulters.sort(key=lambda u: u.total_due, reverse=True)
        context["defaulters"] = defaulters

    return render(request, "society/Admin/Admin_finance.html", context)


@role_required(allowed_roles=["Admin"])
def AdminAddPaymentView(request):
    if request.method == "POST":
        form = AdminPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment recorded successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("admin_finance")


@role_required(allowed_roles=["Admin"])
def AdminMarkPaidView(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.payment_status = "completed"
    payment.save()
    messages.success(request, "Payment marked as completed.")
    return redirect("admin_finance")


@role_required(allowed_roles=["Admin"])
def AdminConfirmBookingView(request, booking_id):
    booking = get_object_or_404(FacilityBooking, id=booking_id)
    booking.booking_status = "confirmed"
    booking.save()
    messages.success(request, f"Booking for '{booking.facility.facility_name}' confirmed.")
    return redirect("admin_finance")


@role_required(allowed_roles=["Admin"])
def AdminCancelBookingView(request, booking_id):
    booking = get_object_or_404(FacilityBooking, id=booking_id)
    booking.booking_status = "cancelled"
    booking.save()
    messages.warning(request, f"Booking for '{booking.facility.facility_name}' cancelled.")
    return redirect("admin_finance")


# ================================================================
# ADMIN — COMMUNITY
# ================================================================
@role_required(allowed_roles=["Admin"])
def AdminCommunityView(request):
    notice_tab = request.GET.get("notice_tab", "all")

    notices_qs = Notice.objects.select_related("created_by").order_by("-created_at")
    if notice_tab != "all":
        notices_qs = notices_qs.filter(target_audience=notice_tab)

    polls_qs = Poll.objects.prefetch_related("votes").order_by("-created_at")
    polls = []
    for poll in polls_qs:
        yes_count   = poll.votes.filter(vote="yes").count()
        no_count    = poll.votes.filter(vote="no").count()
        total_votes = yes_count + no_count
        poll.yes_count   = yes_count
        poll.no_count    = no_count
        poll.total_votes = total_votes
        poll.yes_pct     = int((yes_count / total_votes) * 100) if total_votes else 0
        poll.no_pct      = int((no_count  / total_votes) * 100) if total_votes else 0
        polls.append(poll)

    notice_form = AdminNoticeForm()
    poll_form   = AdminPollForm()

    context = {
        "notices":          notices_qs,
        "polls":            polls,
        "notice_tab":       notice_tab,
        "notice_form":      notice_form,
        "poll_form":        poll_form,
        "total_notices":    Notice.objects.count(),
        "resident_notices": Notice.objects.filter(target_audience="resident").count(),
        "active_polls":     Poll.objects.filter(status="active").count(),
        "total_votes":      PollVote.objects.count(),
        "pending_count":    _pending_count(),   # ← sidebar badge
    }
    return render(request, "society/Admin/Admin_community.html", context)


@role_required(allowed_roles=["Admin"])
def AdminMaintenanceView(request):
    config        = MaintenanceConfig.get()
    config_form   = MaintenanceConfigForm(initial={
        "monthly_amount": config.monthly_amount,
        "due_day":        config.due_day,
    })
    generate_form = GenerateDuesForm()

    paid_dues       = MaintenanceDue.objects.filter(status="paid").count()
    pending_dues    = MaintenanceDue.objects.filter(status="pending").count()
    overdue_dues    = MaintenanceDue.objects.filter(status="overdue").count()
    total_collected = MaintenanceDue.objects.filter(status="paid").aggregate(t=Sum("amount"))["t"] or 0
    total_pending   = MaintenanceDue.objects.filter(status__in=["pending", "overdue"]).aggregate(t=Sum("amount"))["t"] or 0

    month_filter  = request.GET.get("month", "")
    status_filter = request.GET.get("status", "all")
    search_query  = request.GET.get("q", "").strip()

    dues_qs = MaintenanceDue.objects.select_related("resident").order_by("-due_month", "resident__first_name")

    if month_filter:
        dues_qs = dues_qs.filter(due_month__startswith=month_filter)
    if status_filter != "all":
        dues_qs = dues_qs.filter(status=status_filter)
    if search_query:
        dues_qs = dues_qs.filter(
            Q(resident__first_name__icontains=search_query) |
            Q(resident__last_name__icontains=search_query)  |
            Q(resident__unit_number__icontains=search_query)
        )

    paginator = Paginator(dues_qs, 20)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    context = {
        "config":          config,
        "config_form":     config_form,
        "generate_form":   generate_form,
        "paid_dues":       paid_dues,
        "pending_dues":    pending_dues,
        "overdue_dues":    overdue_dues,
        "total_collected": total_collected,
        "total_pending":   total_pending,
        "dues":            page_obj,
        "page_obj":        page_obj,
        "is_paginated":    page_obj.has_other_pages(),
        "month_filter":    month_filter,
        "status_filter":   status_filter,
        "search_query":    search_query,
        "pending_count":   _pending_count(),   # ← sidebar badge
    }
    return render(request, "society/Admin/Admin_maintenance.html", context)


@role_required(allowed_roles=["Admin"])
def AdminSaveMaintenanceConfigView(request):
    if request.method == "POST":
        form = MaintenanceConfigForm(request.POST)
        if form.is_valid():
            config                = MaintenanceConfig.get()
            config.monthly_amount = form.cleaned_data["monthly_amount"]
            config.due_day        = form.cleaned_data["due_day"]
            config.updated_by     = request.user
            config.save()
            messages.success(request, f"Config saved — ₹{config.monthly_amount}/month, due by {config.due_day}th.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("admin_maintenance")


@role_required(allowed_roles=["Admin"])
def AdminGenerateDuesView(request):
    if request.method == "POST":
        form = GenerateDuesForm(request.POST)
        if form.is_valid():
            month_str     = form.cleaned_data["month"]
            custom_amount = form.cleaned_data.get("custom_amount")
            config        = MaintenanceConfig.get()
            amount        = custom_amount if custom_amount else config.monthly_amount

            due_month = date.fromisoformat(month_str)
            last_day  = calendar.monthrange(due_month.year, due_month.month)[1]
            due_day   = min(config.due_day, last_day)
            due_date  = due_month.replace(day=due_day)

            # ── Only generate dues for approved active residents ──────────────
            residents = User.objects.filter(role="Resident", status="active")
            created = skipped = 0

            for resident in residents:
                _, was_created = MaintenanceDue.objects.get_or_create(
                    resident=resident,
                    due_month=due_month,
                    defaults={
                        "amount":   amount,
                        "due_date": due_date,
                        "status":   "pending",
                    }
                )
                if was_created:
                    created += 1
                    if date.today() > due_date:
                        MaintenanceDue.objects.filter(
                            resident=resident, due_month=due_month
                        ).update(status="overdue")
                else:
                    skipped += 1

            messages.success(
                request,
                f"Generated {created} dues for {due_month.strftime('%B %Y')} — {skipped} already existed."
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("admin_maintenance")


@role_required(allowed_roles=["Admin"])
def AdminMarkDuePaidView(request, due_id):
    due = get_object_or_404(MaintenanceDue, id=due_id)
    if due.status not in ("paid", "waived"):
        payment = Payment.objects.create(
            resident       = due.resident,
            amount         = due.amount,
            payment_type   = "maintenance",
            payment_date   = date.today(),
            payment_status = "completed",
        )
        due.status  = "paid"
        due.paid_on = date.today()
        due.payment = payment
        due.save()
        messages.success(
            request,
            f"Marked paid — {due.resident.first_name} {due.resident.last_name} ({due.due_month.strftime('%B %Y')})."
        )
    return redirect("admin_maintenance")


@role_required(allowed_roles=["Admin"])
def AdminWaiveDueView(request, due_id):
    due = get_object_or_404(MaintenanceDue, id=due_id)
    if request.method == "POST":
        due.status = "waived"
        due.note   = request.POST.get("note", "").strip()
        due.save()
        messages.success(
            request,
            f"Due waived — {due.resident.first_name} {due.resident.last_name} ({due.due_month.strftime('%B %Y')})."
        )
    return redirect("admin_maintenance")


@role_required(allowed_roles=["Admin"])
def AdminMarkOverdueView(request):
    updated = MaintenanceDue.objects.filter(
        status="pending", due_date__lt=date.today()
    ).update(status="overdue")
    messages.warning(request, f"{updated} dues marked as overdue.")
    return redirect("admin_maintenance")


@role_required(allowed_roles=["Admin"])
def AdminDeleteDueView(request, due_id):
    due   = get_object_or_404(MaintenanceDue, id=due_id)
    month = due.due_month.strftime("%B %Y")
    name  = f"{due.resident.first_name} {due.resident.last_name}"
    due.delete()
    messages.success(request, f"Due deleted — {name} ({month}).")
    return redirect("admin_maintenance")


@role_required(allowed_roles=["Admin"])
def AdminExportDuesView(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="maintenance_dues.csv"'
    writer = csv.writer(response)
    writer.writerow(["Resident", "Unit", "Month", "Amount", "Due Date", "Status", "Paid On"])
    for d in MaintenanceDue.objects.select_related("resident").order_by("-due_month"):
        writer.writerow([
            f"{d.resident.first_name} {d.resident.last_name}",
            getattr(d.resident, "unit_number", "—"),
            d.due_month.strftime("%B %Y"),
            d.amount,
            d.due_date,
            d.status,
            d.paid_on or "—",
        ])
    return response


@role_required(allowed_roles=["Admin"])
def AdminAddNoticeView(request):
    if request.method == "POST":
        form = AdminNoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            messages.success(request, f"Notice '{notice.title}' posted successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("admin_community")


@role_required(allowed_roles=["Admin"])
def AdminDeleteNoticeView(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    notice.delete()
    messages.success(request, "Notice deleted.")
    return redirect("admin_community")


@role_required(allowed_roles=["Admin"])
def AdminAddPollView(request):
    if request.method == "POST":
        form = AdminPollForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.created_by = request.user
            poll.status     = "active"
            poll.save()
            messages.success(request, "Poll created successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("admin_community")


@role_required(allowed_roles=["Admin"])
def AdminClosePollView(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    poll.status    = "closed"
    poll.closed_at = timezone.now()
    poll.save()
    messages.success(request, "Poll closed.")
    return redirect("admin_community")


@role_required(allowed_roles=["Admin"])
def AdminDeletePollView(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    poll.delete()
    messages.success(request, "Poll deleted.")
    return redirect("admin_community")


# ================================================================
# ADMIN — SETTINGS
# ================================================================
@role_required(allowed_roles=["Admin"])
def AdminSettingsView(request):
    saved = request.session.get("society_settings", {})

    society_form  = AdminSocietySettingsForm(initial=saved)
    password_form = AdminChangePasswordForm()
    facility_form = AdminFacilityForm()
    facilities    = Facility.objects.all().order_by("facility_name")

    context = {
        "society_form":  society_form,
        "password_form": password_form,
        "facility_form": facility_form,
        "facilities":    facilities,
        "settings":      saved,
        "pending_count": _pending_count(),   # ← sidebar badge
    }
    return render(request, "society/Admin/Admin_settings.html", context)


@role_required(allowed_roles=["Admin"])
def AdminSaveSettingsView(request):
    if request.method == "POST":
        section = request.POST.get("section")
        current = request.session.get("society_settings", {})

        if section == "society":
            form = AdminSocietySettingsForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                current.update({
                    "society_name":    cd.get("society_name", ""),
                    "total_units":     cd.get("total_units"),
                    "maintenance_fee": str(cd.get("maintenance_fee", "")),
                    "address":         cd.get("address", ""),
                    "contact_email":   cd.get("contact_email", ""),
                    "contact_phone":   cd.get("contact_phone", ""),
                })
                request.session["society_settings"] = current
                messages.success(request, "Society profile saved.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")

        elif section == "notifications":
            current.update({
                "notify_complaint": "notify_complaint" in request.POST,
                "notify_payment":   "notify_payment"   in request.POST,
                "notify_visitor":   "notify_visitor"   in request.POST,
                "notify_booking":   "notify_booking"   in request.POST,
            })
            request.session["society_settings"] = current
            messages.success(request, "Notification preferences saved.")

    return redirect("admin_settings")


@role_required(allowed_roles=["Admin"])
def AdminChangePasswordView(request):
    if request.method == "POST":
        form = AdminChangePasswordForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if not request.user.check_password(cd["current_password"]):
                messages.error(request, "Current password is incorrect.")
            else:
                request.user.set_password(cd["new_password"])
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password updated successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("admin_settings")


@role_required(allowed_roles=["Admin"])
def AdminAddFacilityView(request):
    if request.method == "POST":
        form = AdminFacilityForm(request.POST)
        if form.is_valid():
            facility = form.save(commit=False)
            facility.availability_status = "available"
            facility.save()
            messages.success(request, f"Facility '{facility.facility_name}' added.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("admin_settings")


@role_required(allowed_roles=["Admin"])
def AdminToggleFacilityView(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    facility.availability_status = (
        "unavailable" if facility.availability_status == "available" else "available"
    )
    facility.save()
    messages.success(request, f"'{facility.facility_name}' status updated.")
    return redirect("admin_settings")


@role_required(allowed_roles=["Admin"])
def AdminExportAllView(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="society_export.csv"'
    writer = csv.writer(response)

    writer.writerow(["=== RESIDENTS ==="])
    writer.writerow(["Name", "Email", "Unit", "Mobile", "Active", "Complaints", "Pending Payments", "Joined"])
    for r in User.objects.filter(role="Resident", status__in=["active", "inactive", "blocked"]).order_by("first_name"):
        writer.writerow([
            f"{r.first_name} {r.last_name}",
            r.email,
            getattr(r, "unit_number", "—"),
            getattr(r, "mobile_number", "—"),
            "Yes" if r.is_active else "No",
            Complaint.objects.filter(resident=r).count(),
            Payment.objects.filter(resident=r, payment_status="pending").count(),
            r.created_at.strftime("%d %b %Y") if r.created_at else "—",
        ])

    writer.writerow([])
    writer.writerow(["=== PAYMENTS ==="])
    writer.writerow(["Resident", "Unit", "Type", "Amount", "Status", "Date"])
    for p in Payment.objects.select_related("resident").order_by("-payment_date"):
        writer.writerow([
            f"{p.resident.first_name} {p.resident.last_name}",
            getattr(p.resident, "unit_number", "—"),
            p.get_payment_type_display(),
            p.amount,
            p.payment_status,
            p.payment_date,
        ])

    return response


# ================================================================
# ADMIN — VISITOR LOGS
# ================================================================
@role_required(allowed_roles=["Admin"])
def AdminVisitorLogsView(request):
    today = date.today()

    date_filter   = request.GET.get("date", "")
    type_filter   = request.GET.get("type", "all")
    status_filter = request.GET.get("status", "all")
    search_query  = request.GET.get("q", "").strip()

    visitors = (
        Visitor.objects
        .select_related("resident", "guard")
        .order_by("-created_at")
    )

    if date_filter:
        visitors = visitors.filter(expected_date=date_filter)
    if type_filter != "all":
        visitors = visitors.filter(visitor_type=type_filter)
    if status_filter != "all":
        visitors = visitors.filter(entry_status=status_filter)
    if search_query:
        visitors = visitors.filter(
            Q(visitor_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="visitor_logs.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Visitor Name", "Mobile", "Unit", "Resident", "Registered By",
            "Type", "Expected Date", "Entry Time", "Exit Time",
            "Vehicle", "Guard", "Approval Status", "Entry Status"
        ])
        for v in visitors:
            writer.writerow([
                v.visitor_name,
                v.mobile_number,
                getattr(v.resident, "unit_number", "—"),
                f"{v.resident.first_name} {v.resident.last_name}".strip(),
                v.get_registered_by_display(),
                v.get_visitor_type_display(),
                v.expected_date,
                v.entry_time.strftime("%I:%M %p") if v.entry_time else "—",
                v.exit_time.strftime("%I:%M %p")  if v.exit_time  else "—",
                v.vehicle_number or "—",
                f"{v.guard.first_name} {v.guard.last_name}".strip() if v.guard else "—",
                v.get_approval_status_display(),
                v.get_entry_status_display(),
            ])
        return response

    total_today      = Visitor.objects.filter(expected_date=today).count()
    currently_inside = Visitor.objects.filter(entry_status="inside").count()
    total_deliveries = Visitor.objects.filter(expected_date=today, visitor_type="delivery").count()
    total_denied     = Visitor.objects.filter(expected_date=today, entry_status="denied").count()

    paginator = Paginator(visitors, 25)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    context = {
        "active_page":      "vislog",
        "visitors":         page_obj,
        "page_obj":         page_obj,
        "is_paginated":     page_obj.has_other_pages(),
        "date_filter":      date_filter,
        "type_filter":      type_filter,
        "status_filter":    status_filter,
        "search_query":     search_query,
        "total_today":      total_today,
        "currently_inside": currently_inside,
        "total_deliveries": total_deliveries,
        "total_denied":     total_denied,
        "pending_count":    _pending_count(),   # ← sidebar badge
    }
    return render(request, "society/Admin/Admin_visitor_logs.html", context)


@role_required(allowed_roles=["Admin"])
def AdminMarkAllReadView(request):
    from .models import Notification
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        from django.http import JsonResponse
        return JsonResponse({"status": "ok"})
    return redirect(request.META.get("HTTP_REFERER", "admin_dashboard"))


# ================================================================
# RESIDENT VIEWS
# ================================================================
@role_required(allowed_roles=["Resident"])
def ResidentDashboardView(request):
    user = request.user
    user_complaints     = Complaint.objects.filter(resident=user)
    total_complaints    = user_complaints.count()
    resolved_complaints = user_complaints.filter(status="resolved").count()
    pending_visitors    = Visitor.objects.filter(
        resident=user, registered_by="guard", approval_status="pending"
    ).count()
    active_booking = FacilityBooking.objects.filter(
        booked_by=user, booking_status="confirmed"
    ).count()

    from .models import Notice, Payment, MaintenanceDue
    recent_notices  = Notice.objects.filter(
        target_audience__in=["all", "resident"]
    ).order_by("-created_at")[:5]

    recent_payments = Payment.objects.filter(resident=user).order_by("-created_at")[:5]

    current_due = MaintenanceDue.objects.filter(
        resident=user, status__in=["pending", "overdue"]
    ).order_by("-due_month").first()

    context = {
        "total_complaints":    total_complaints,
        "resolved_complaints": resolved_complaints,
        "active_booking":      active_booking,
        "pending_visitors":    pending_visitors,
        "maintenance_amount":  current_due.amount if current_due else 0,
        "maintenance_due":     current_due,
        "recent_notices":      recent_notices,
        "recent_payments":     recent_payments,
        "unread_notif_count":  Notification.objects.filter(user=user, is_read=False).count(),
    }
    return render(request, "society/Resident/Resident_dashboard.html", context)


@role_required(allowed_roles=["Resident"])
def visitor_pass(request):
    if request.method == "POST":
        form = VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.resident        = request.user
            visitor.registered_by   = "resident"
            visitor.approval_status = "approved"
            visitor.entry_status    = "waiting"
            visitor.save()
            messages.success(request, f"Visitor pass created for '{visitor.visitor_name}'.")
            return redirect("visitor_pass")
    else:
        form = VisitorForm()

    visitors = Visitor.objects.filter(
        resident=request.user, registered_by="resident"
    ).order_by("-created_at")

    return render(request, "society/Resident/visitor_pass.html", {
        "form":               form,
        "visitors":           visitors,
        "unread_notif_count": Notification.objects.filter(user=request.user, is_read=False).count(),
        "pending_visitors":   Visitor.objects.filter(resident=request.user, registered_by="guard", approval_status="pending").count(),
    })


@role_required(allowed_roles=["Resident"])
def visitor_approvals(request):
    user = request.user
    pending = Visitor.objects.filter(
        resident=user, registered_by="guard", approval_status="pending"
    ).order_by("-created_at")
    history = Visitor.objects.filter(
        resident=user, registered_by="guard", approval_status__in=["approved", "rejected"]
    ).order_by("-created_at")[:20]
    return render(request, "society/Resident/visitor_approval.html", {
        "pending":            pending,
        "history":            history,
        "unread_notif_count": Notification.objects.filter(user=user, is_read=False).count(),
        "pending_visitors":   pending.count(),
    })


@role_required(allowed_roles=["Resident"])
def visitor_decision(request, visitor_id, decision):
    from django.http import JsonResponse

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    visitor = get_object_or_404(
        Visitor, id=visitor_id, resident=request.user,
        registered_by="guard", approval_status="pending"
    )

    if decision == "approve":
        visitor.approval_status = "approved"
        visitor.save()
        if visitor.guard:
            Notification.objects.create(
                user=visitor.guard,
                message=f"Resident approved '{visitor.visitor_name}'. You may allow entry."
            )
        if is_ajax:
            return JsonResponse({"status": "approved", "visitor": visitor.visitor_name})
        messages.success(request, f"'{visitor.visitor_name}' approved.")

    elif decision == "reject":
        visitor.approval_status = "rejected"
        visitor.entry_status    = "denied"
        visitor.save()
        if visitor.guard:
            Notification.objects.create(
                user=visitor.guard,
                message=f"Resident rejected '{visitor.visitor_name}'. Do not allow entry."
            )
        if is_ajax:
            return JsonResponse({"status": "rejected", "visitor": visitor.visitor_name})
        messages.warning(request, f"'{visitor.visitor_name}' rejected.")

    else:
        if is_ajax:
            return JsonResponse({"error": "invalid_decision"}, status=400)

    return redirect("resident_visitor_approval")


@role_required(allowed_roles=["Resident"])
def complaints(request):
    user = request.user
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint          = form.save(commit=False)
            complaint.resident = user
            complaint.save()
            messages.success(request, "Complaint submitted successfully.")
            return redirect("complaints")
    else:
        form = ComplaintForm()

    complaints_qs = Complaint.objects.filter(resident=user).order_by("-created_at")

    context = {
        "form":               form,
        "complaints":         complaints_qs,
        "pending_count":      complaints_qs.filter(status="pending").count(),
        "inprogress_count":   complaints_qs.filter(status="in_progress").count(),
        "resolved_count":     complaints_qs.filter(status="resolved").count(),
        "unread_notif_count": Notification.objects.filter(user=user, is_read=False).count(),
        "pending_visitors":   Visitor.objects.filter(resident=user, registered_by="guard", approval_status="pending").count(),
    }
    return render(request, "society/Resident/Resident_complaints.html", context)


@role_required(allowed_roles=["Resident"])
def facility_booking(request):
    if request.method == "POST" and request.POST.get("action") == "book":
        facility_id  = request.POST.get("facility_id")
        booking_date = request.POST.get("booking_date")
        time_slot    = request.POST.get("time_slot")
        amount       = request.POST.get("amount", 0)

        errors = []
        if not facility_id:
            errors.append("Please select a facility.")
        if not booking_date:
            errors.append("Please choose a booking date.")
        if not time_slot:
            errors.append("Please choose a time slot.")

        if not errors:
            try:
                facility = Facility.objects.get(id=facility_id, availability_status="available")
                duplicate = FacilityBooking.objects.filter(
                    facility=facility,
                    booking_date=booking_date,
                    time_slot=time_slot,
                    booking_status__in=["pending", "confirmed"],
                ).exists()
                if duplicate:
                    messages.error(request, "That time slot is already booked. Please choose another.")
                else:
                    FacilityBooking.objects.create(
                        facility=facility,
                        booked_by=request.user,
                        booking_date=booking_date,
                        time_slot=time_slot,
                        amount=amount,
                        booking_status="pending",
                        payment_status="pending",
                    )
                    messages.success(request, f"Booking request submitted for '{facility.facility_name}'. Awaiting admin confirmation.")
            except Facility.DoesNotExist:
                messages.error(request, "Invalid facility selected.")
        else:
            for e in errors:
                messages.error(request, e)

        return redirect("facility_booking")

    facilities = Facility.objects.all().order_by("facility_name")
    bookings   = FacilityBooking.objects.filter(
        booked_by=request.user
    ).select_related("facility").order_by("-created_at")

    return render(request, "society/Resident/booking.html", {
        "facilities":         facilities,
        "bookings":           bookings,
        "unread_notif_count": Notification.objects.filter(user=request.user, is_read=False).count(),
        "pending_visitors":   Visitor.objects.filter(resident=request.user, registered_by="guard", approval_status="pending").count(),
    })


@role_required(allowed_roles=["Resident"])
def community_notice(request):
    from .models import Notice, Poll, PollVote
    notices = Notice.objects.filter(
        target_audience__in=["all", "resident"]
    ).order_by("-created_at")

    polls_qs = Poll.objects.filter(status="active").order_by("-created_at")

    polls = []
    for poll in polls_qs:
        total   = poll.votes.count()
        yes_ct  = poll.votes.filter(vote="yes").count()
        no_ct   = poll.votes.filter(vote="no").count()
        try:
            user_vote = poll.votes.get(voter=request.user).vote
        except PollVote.DoesNotExist:
            user_vote = None
        poll.total_votes = total
        poll.yes_pct     = round((yes_ct / total * 100) if total else 0)
        poll.no_pct      = round((no_ct  / total * 100) if total else 0)
        poll.user_vote   = user_vote
        polls.append(poll)

    return render(request, "society/Resident/Resident_community.html", {
        "notices":            notices,
        "polls":              polls,
        "unread_notif_count": Notification.objects.filter(user=request.user, is_read=False).count(),
        "pending_visitors":   Visitor.objects.filter(resident=request.user, registered_by="guard", approval_status="pending").count(),
    })


@role_required(allowed_roles=["Resident"])
def resident_settings(request):
    return render(request, "society/Resident/Resident_settings.html", {
        "unread_notif_count": Notification.objects.filter(user=request.user, is_read=False).count(),
        "pending_visitors":   Visitor.objects.filter(resident=request.user, registered_by="guard", approval_status="pending").count(),
    })


@role_required(allowed_roles=["Resident"])
def resident_change_password(request):
    if request.method == "POST":
        current  = request.POST.get("current_password", "")
        new_pwd  = request.POST.get("new_password", "")
        confirm  = request.POST.get("confirm_password", "")

        if not request.user.check_password(current):
            messages.error(request, "Current password is incorrect.")
        elif new_pwd != confirm:
            messages.error(request, "New passwords do not match.")
        elif len(new_pwd) < 8:
            messages.error(request, "New password must be at least 8 characters.")
        else:
            request.user.set_password(new_pwd)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password changed successfully.")

    return redirect("resident_settings")


@role_required(allowed_roles=["Resident"])
def resident_payments(request):
    from .models import MaintenanceDue
    payments     = Payment.objects.filter(resident=request.user).order_by("-created_at")
    dues         = MaintenanceDue.objects.filter(resident=request.user).order_by("-due_month")
    pending_dues = dues.filter(status__in=["pending", "overdue"])
    total_due    = pending_dues.aggregate(t=Sum("amount"))["t"] or 0

    return render(request, "society/Resident/Resident_payments.html", {
        "payments":           payments,
        "dues":               dues,
        "pending_dues":       pending_dues,
        "total_due":          total_due,
        "unread_notif_count": Notification.objects.filter(user=request.user, is_read=False).count(),
        "pending_visitors":   Visitor.objects.filter(resident=request.user, registered_by="guard", approval_status="pending").count(),
    })


@role_required(allowed_roles=["Resident"])
def resident_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    unread_count  = notifications.filter(is_read=False).count()
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "society/Resident/Resident_notifications.html", {
        "notifications":      notifications,
        "unread_count":       unread_count,
        "unread_notif_count": 0,
    })


@role_required(allowed_roles=["Resident"])
def resident_poll_vote(request, poll_id, vote):
    from django.http import JsonResponse

    poll = get_object_or_404(Poll, id=poll_id, status="active")
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    already_voted = PollVote.objects.filter(poll=poll, voter=request.user).exists()
    if already_voted:
        if is_ajax:
            return JsonResponse({"error": "already_voted"}, status=400)
        messages.warning(request, "You have already voted on this poll.")
        return redirect("community_notice")

    if vote in ["yes", "no"]:
        PollVote.objects.create(poll=poll, voter=request.user, vote=vote)

        total  = poll.votes.count()
        yes_ct = poll.votes.filter(vote="yes").count()
        no_ct  = poll.votes.filter(vote="no").count()
        yes_pct = round((yes_ct / total * 100) if total else 0)
        no_pct  = round((no_ct  / total * 100) if total else 0)

        if is_ajax:
            return JsonResponse({
                "yes_pct":   yes_pct,
                "no_pct":    no_pct,
                "yes_count": yes_ct,
                "no_count":  no_ct,
                "total":     total,
            })

        messages.success(request, f"Your vote '{vote}' has been recorded.")
    else:
        if is_ajax:
            return JsonResponse({"error": "invalid_vote"}, status=400)
        messages.error(request, "Invalid vote.")

    return redirect("community_notice")


@role_required(allowed_roles=["Resident"])
def ResidentMarkAllReadView(request):
    from .models import Notification
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        from django.http import JsonResponse
        return JsonResponse({"status": "ok"})
    return redirect(request.META.get("HTTP_REFERER", "resident_dashboard"))


# ================================================================
# SECURITY GUARD VIEWS
# ================================================================
@role_required(allowed_roles=["Securityguard"])
def SecurityDashboardView(request):
    today = date.today()
    today_visitors_qs = (
        Visitor.objects.filter(expected_date=today)
        .select_related("resident", "guard")
        .order_by("-created_at")
    )

    visitor_breakdown = [
        {"label": "Guests",         "count": today_visitors_qs.filter(visitor_type="guest").count(),       "badge": "badge-info"},
        {"label": "Deliveries",     "count": today_visitors_qs.filter(visitor_type="delivery").count(),    "badge": "badge-purple"},
        {"label": "Maintenance",    "count": today_visitors_qs.filter(visitor_type="maintenance").count(), "badge": "badge-warning"},
        {"label": "Staff",          "count": today_visitors_qs.filter(visitor_type="staff").count(),       "badge": "badge-gray"},
        {"label": "Pre-Registered", "count": today_visitors_qs.filter(registered_by="resident").count(),  "badge": "badge-info"},
        {"label": "Guard-Logged",   "count": today_visitors_qs.filter(registered_by="guard").count(),     "badge": "badge-warning"},
    ]

    context = {
        "today_date":             today,
        "total_today":            today_visitors_qs.count(),
        "currently_inside":       today_visitors_qs.filter(entry_status="inside").count(),
        "pending_approval":       today_visitors_qs.filter(registered_by="guard", approval_status="pending").count(),
        "pending_approval_count": today_visitors_qs.filter(registered_by="guard", approval_status="pending").count(),
        "total_denied":           today_visitors_qs.filter(entry_status="denied").count(),
        "today_visitors":         today_visitors_qs[:8],
        "pending_visitors":       today_visitors_qs.filter(registered_by="guard", approval_status="pending"),
        "pre_approved_visitors":  today_visitors_qs.filter(registered_by="resident", approval_status="approved"),
        "visitor_breakdown":      visitor_breakdown,
        "unread_notif_count":     Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, "society/Securityguard/Security_dashboard.html", context)


@role_required(allowed_roles=["Securityguard"])
def guard_log_visitor(request):
    if request.method == "POST":
        form = GuardVisitorForm(request.POST, request.FILES)
        form.fields["resident"].label_from_instance = lambda u: f"{u.first_name} {u.last_name} — Unit {u.unit_number or '—'}"
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.guard           = request.user
            visitor.expected_date   = date.today()
            visitor.registered_by   = "guard"
            visitor.approval_status = "pending"
            visitor.entry_status    = "waiting"
            visitor.save()

            Notification.objects.create(
                user=visitor.resident,
                message=(
                    f"🔔 Visitor '{visitor.visitor_name}' "
                    f"({visitor.get_visitor_type_display()}) "
                    f"has arrived at the gate and is waiting for your approval."
                )
            )
            messages.success(
                request,
                f"'{visitor.visitor_name}' logged successfully. Resident has been notified."
            )
            return redirect("guard_log_visitor")
        else:
            today_visitors = (
                Visitor.objects.filter(expected_date=date.today())
                .select_related("resident", "guard")
                .order_by("-created_at")
            )
            return render(request, "society/Securityguard/guard_log_visitor.html", {
                "form":                   form,
                "today_visitors":         today_visitors,
                "show_log_modal":         True,
                "total_today":            today_visitors.count(),
                "currently_inside":       today_visitors.filter(entry_status="inside").count(),
                "pending_approval_count": today_visitors.filter(approval_status="pending", registered_by="guard").count(),
                "total_denied":           today_visitors.filter(entry_status="denied").count(),
                "search_query":           "",
                "type_filter":            "all",
                "status_filter":          "all",
            })
    else:
        form = GuardVisitorForm()
        form.fields["resident"].label_from_instance = lambda u: f"{u.first_name} {u.last_name} — Unit {u.unit_number or '—'}"

    search_query  = request.GET.get("q", "").strip()
    type_filter   = request.GET.get("type", "all")
    status_filter = request.GET.get("status", "all")

    today_visitors_qs = (
        Visitor.objects.filter(expected_date=date.today())
        .select_related("resident", "guard")
        .order_by("-created_at")
    )

    if search_query:
        today_visitors_qs = today_visitors_qs.filter(
            Q(visitor_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    if type_filter != "all":
        today_visitors_qs = today_visitors_qs.filter(visitor_type=type_filter)
    if status_filter != "all":
        today_visitors_qs = today_visitors_qs.filter(entry_status=status_filter)

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="visitor_log_today.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Visitor Name", "Mobile", "Type", "Vehicle",
            "Resident", "Unit", "Registered By",
            "Approval Status", "Entry Status", "Entry Time", "Exit Time"
        ])
        for v in today_visitors_qs:
            writer.writerow([
                v.visitor_name,
                v.mobile_number,
                v.get_visitor_type_display(),
                v.vehicle_number or "—",
                f"{v.resident.first_name} {v.resident.last_name}",
                getattr(v.resident, "unit_number", "—"),
                v.registered_by,
                v.get_approval_status_display(),
                v.get_entry_status_display(),
                v.entry_time.strftime("%d %b %Y %I:%M %p") if v.entry_time else "—",
                v.exit_time.strftime("%d %b %Y %I:%M %p")  if v.exit_time  else "—",
            ])
        return response

    paginator = Paginator(today_visitors_qs, 20)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    context = {
        "form":                   form,
        "today_visitors":         page_obj,
        "page_obj":               page_obj,
        "is_paginated":           page_obj.has_other_pages(),
        "search_query":           search_query,
        "type_filter":            type_filter,
        "status_filter":          status_filter,
        "total_today":            Visitor.objects.filter(expected_date=date.today()).count(),
        "currently_inside":       Visitor.objects.filter(expected_date=date.today(), entry_status="inside").count(),
        "pending_approval_count": Visitor.objects.filter(expected_date=date.today(), registered_by="guard", approval_status="pending").count(),
        "pre_approved_count":     Visitor.objects.filter(expected_date=date.today(), registered_by="resident", approval_status="approved", entry_status="waiting").count(),
        "total_denied":           Visitor.objects.filter(expected_date=date.today(), entry_status="denied").count(),
        "unread_notif_count":     Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, "society/Securityguard/guard_log_visitor.html", context)


@role_required(allowed_roles=["Securityguard"])
def guard_update_entry(request, visitor_id, action):
    visitor = get_object_or_404(Visitor, id=visitor_id)

    if action == "enter":
        if visitor.approval_status != "approved":
            messages.error(
                request,
                f"Cannot allow entry — '{visitor.visitor_name}' has not been approved by the resident yet."
            )
            return redirect("guard_log_visitor")
        visitor.entry_status = "inside"
        visitor.entry_time   = timezone.now()
        visitor.guard        = request.user
        visitor.save()

        Notification.objects.create(
            user=visitor.resident,
            message=(
                f"🚶 Your visitor '{visitor.visitor_name}' has entered the society "
                f"at {visitor.entry_time.strftime('%I:%M %p')}."
            )
        )
        messages.success(request, f"'{visitor.visitor_name}' marked as entered.")

    elif action == "exit":
        visitor.entry_status = "exited"
        visitor.exit_time    = timezone.now()
        visitor.save()

        Notification.objects.create(
            user=visitor.resident,
            message=(
                f"👋 Your visitor '{visitor.visitor_name}' has exited the society "
                f"at {visitor.exit_time.strftime('%I:%M %p')}."
            )
        )
        messages.success(request, f"'{visitor.visitor_name}' marked as exited.")

    elif action == "deny":
        visitor.entry_status    = "denied"
        visitor.approval_status = "rejected"
        visitor.save()
        messages.warning(request, f"'{visitor.visitor_name}' denied entry.")

    return redirect("guard_log_visitor")


@role_required(allowed_roles=["Securityguard"])
def guard_notifications(request):
    notifications_qs = (
        Notification.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    total_count  = notifications_qs.count()
    unread_count = notifications_qs.filter(is_read=False).count()
    read_count   = total_count - unread_count

    notifications_qs.filter(is_read=False).update(is_read=True)

    paginator = Paginator(notifications_qs, 20)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    return render(request, "society/Securityguard/guard_notifications.html", {
        "notifications":  page_obj,
        "page_obj":       page_obj,
        "is_paginated":   page_obj.has_other_pages(),
        "total_count":    total_count,
        "unread_count":   unread_count,
        "read_count":     read_count,
        "unread_notif_count": 0,
    })


@role_required(allowed_roles=["Securityguard"])
def guard_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        from django.http import JsonResponse
        return JsonResponse({"status": "ok"})
    return redirect(request.META.get("HTTP_REFERER", "security_dashboard"))


@role_required(allowed_roles=["Securityguard"])
def guard_settings(request):
    return render(request, "society/Securityguard/guard_settings.html", {
        "unread_notif_count":     Notification.objects.filter(user=request.user, is_read=False).count(),
        "pending_approval_count": Visitor.objects.filter(expected_date=date.today(), registered_by="guard", approval_status="pending").count(),
    })


@role_required(allowed_roles=["Securityguard"])
def guard_change_password(request):
    if request.method == "POST":
        current  = request.POST.get("current_password", "")
        new_pwd  = request.POST.get("new_password", "")
        confirm  = request.POST.get("confirm_password", "")

        if not request.user.check_password(current):
            messages.error(request, "Current password is incorrect.")
        elif new_pwd != confirm:
            messages.error(request, "New passwords do not match.")
        elif len(new_pwd) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        else:
            request.user.set_password(new_pwd)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password updated successfully.")

    return redirect("guard_settings")