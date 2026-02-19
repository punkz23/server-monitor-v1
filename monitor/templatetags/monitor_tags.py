from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Lookup a key in a dictionary"""
    return dictionary.get(key, {})

@register.filter
def get_item(dictionary, key):
    """Return the value for a given key from a dictionary."""
    return dictionary.get(key, {})

@register.filter
def first_item(dictionary):
    """Return the first item of a dictionary"""
    if isinstance(dictionary, dict) and dictionary:
        # Return the value of the first key
        return list(dictionary.values())[0]
    return {}
