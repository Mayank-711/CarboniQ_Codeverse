from django import template

register = template.Library()

@register.filter(name="dict_get")
def dict_get(dictionary, key):
    """Returns the value for a given key in a dictionary, or None if not found."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None
