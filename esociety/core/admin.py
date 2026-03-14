from django.contrib import admin
from .models import User, DemoBooking

# Register your models here.
admin.site.register(User)
admin.site.register(DemoBooking)
