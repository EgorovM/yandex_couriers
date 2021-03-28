from django.contrib import admin

from orders import models


admin.site.register(models.Region)
admin.site.register(models.Order)

