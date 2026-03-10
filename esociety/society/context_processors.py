from .models import Notification
from datetime import date


def security_notifications(request):
    """
    Injects notification data into every template based on user role.
    Safe to register globally — returns empty dict for unauthenticated users.
    """
    if not request.user.is_authenticated:
        return {}

    role = getattr(request.user, 'role', None)

    if role == 'Securityguard':
        notifs = (
            Notification.objects
            .filter(user=request.user)
            .order_by('-created_at')[:8]
        )
        return {
            'guard_notifications':    notifs,
            'unread_notif_count':     Notification.objects.filter(user=request.user, is_read=False).count(),
            'pending_approval_count': _pending_approval_count(request.user),
        }

    if role == 'Admin':
        notifs = (
            Notification.objects
            .filter(user=request.user)
            .order_by('-created_at')[:8]
        )
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'admin_notifications': notifs,
            'unread_notif_count':  unread,
        }

    if role == 'Resident':
        from .models import Visitor
        notifs = (
            Notification.objects
            .filter(user=request.user)
            .order_by('-created_at')[:8]
        )
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        pending_visitors = Visitor.objects.filter(
            resident=request.user,
            registered_by='guard',
            approval_status='pending',
        ).count()
        return {
            'resident_notifications': notifs,       # used by bell dropdown in base
            'unread_notif_count':     unread,        # used by bell badge + sidebar
            'pending_visitors':       pending_visitors,  # used by sidebar badge
        }

    return {}


def _pending_approval_count(guard_user):
    """
    Count visitors logged by this guard today still waiting for resident approval.
    """
    from .models import Visitor
    return Visitor.objects.filter(
        guard=guard_user,
        expected_date=date.today(),
        registered_by='guard',
        approval_status='pending',
    ).count()