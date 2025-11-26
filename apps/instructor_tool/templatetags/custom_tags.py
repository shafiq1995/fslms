from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return dictionary[key] safely in templates."""
    try:
        return dictionary.get(key)
    except Exception:
        return None
