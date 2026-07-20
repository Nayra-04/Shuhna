from django.contrib import admin
from .models import User,MerchantProfile, RepProfile

admin.site.register(User)
admin.site.register(MerchantProfile)
admin.site.register(RepProfile)
