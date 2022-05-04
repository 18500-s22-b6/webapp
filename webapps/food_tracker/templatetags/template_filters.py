# template_filters.py

# https://stackoverflow.com/questions/223990/how-do-i-perform-query-filtering-in-django-templates

from django import template
from ..models import *
from ..constants import *

register = template.Library()

@register.filter
def in_cat(ItemEntry, Category):
    return ItemEntry.filter(type=Category)

@register.filter
def has_unid(id):
    try:
        return ItemEntry.objects.filter(location=Device.objects.get(serial_number=id), type__name="UNKNOWN ITEM").exists()
    except Exception as e:
        return False

@register.filter
def get_status(status):
    status_str = {
        NOT_REGISTERED: "unregistered", 
        ONLINE: "online", 
        OFFLINE: "offline"
    }
    return status_str.get(status, "n/a")

@register.filter
def get_status_style(status):
    status_style = {
        NOT_REGISTERED: "muted",
        ONLINE: "success",
        OFFLINE: "danger"
    }
    return status_style.get(status, "muted")
    
@register.filter
def get_num_of_items(id):
    device = Device.objects.get(serial_number=id)
    return len(ItemEntry.objects.filter(location=device))

@register.filter
def get_num_of_ingredients(id, public=False):
    return len(get_ingredients(id, public))

@register.filter
def get_ingredients(id, public=False):
    if public:
        recipe = PublicRecipe.objects.get(id=id)
    else:
        recipe = Recipe.objects.get(id=id)
    
    ingredients = []
    for i in recipe.ingredients.all():
        ingredients.append(i.name)
    ingredients.sort()
    return ingredients

@register.filter
def in_stock(name, user_id):
    user = User.objects.get(id=user_id)
    items = ItemEntry.objects.filter(location__owner=user)
    for i in items:
        if i.type.name == name:
            return True
    return False