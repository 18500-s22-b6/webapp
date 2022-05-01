# template_filters.py

# https://stackoverflow.com/questions/223990/how-do-i-perform-query-filtering-in-django-templates

from django import template
from ..models import Device, ItemEntry

register = template.Library()

@register.filter
def in_cat(ItemEntry, Category):
    return ItemEntry.filter(type=Category)

@register.filter
def get_status(status):
    status_str = {
        0: "unregistered", 
        1: "online", 
        2: "offline"
    }
    return status_str.get(status, "n/a")

@register.filter
def get_status_style(status):
    status_style = {
        0: "text-muted",
        1: "text-success",
        2: "text-danger"
    }
    return status_style.get(status, "text-muted")
    
@register.filter
def get_num_of_items(id):
    device = Device.objects.get(serial_number=id)
    return len(ItemEntry.objects.filter(location=device))