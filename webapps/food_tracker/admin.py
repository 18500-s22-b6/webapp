from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from food_tracker.models import *

class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'phone_number', 'image_url'
        )
    readonly_fields = ('last_ping',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Device)
admin.site.register(Category)
admin.site.register(ItemEntry)
admin.site.register(Recipe)
admin.site.register(PublicRecipe)
admin.site.register(IconicImage)
