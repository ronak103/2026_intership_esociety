from django.contrib import admin

from .models import Visitor,Complaint,Notice,Facility,Payment,FacilityBooking,Notification,EmergencyAlert,MaintenanceDue, MaintenanceConfig 
# Register your models here.

admin.site.register(Visitor)    
admin.site.register(Complaint)
admin.site.register(Notice)
admin.site.register(Facility)
admin.site.register(Payment)
admin.site.register(FacilityBooking)
admin.site.register(Notification)
admin.site.register(EmergencyAlert)
admin.site.register(MaintenanceDue)
admin.site.register(MaintenanceConfig)