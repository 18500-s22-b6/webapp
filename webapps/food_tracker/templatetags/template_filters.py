# template_filters.py

# https://stackoverflow.com/questions/223990/how-do-i-perform-query-filtering-in-django-templates

from django import template

register = template.Library()

@register.filter
def in_cat(ItemEntry, Category):
    return ItemEntry.filter(type=Category)