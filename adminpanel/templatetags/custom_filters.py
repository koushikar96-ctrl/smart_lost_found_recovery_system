from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Custom filter to get a dictionary item by key"""
    try:
        return dictionary.get(str(key)) or dictionary.get(int(key))
    except Exception:
        return ""
