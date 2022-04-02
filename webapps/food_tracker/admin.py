from django.contrib import admin
from food_tracker.models import *

admin.site.register(User)
admin.site.register(Device)
admin.site.register(Category)
admin.site.register(ItemEntry)