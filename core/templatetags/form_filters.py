# core/templatetags/form_filters.py
from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        return field.as_widget(attrs={"class": css_class})
    return field