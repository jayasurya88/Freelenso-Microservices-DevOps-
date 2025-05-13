from django import template

register = template.Library()

@register.filter
def get_item(value, key):
    """
    Get item from dictionary or rating distribution list
    """
    if isinstance(value, dict):
        return value.get(str(key), {'count': 0})
    elif isinstance(value, list):
        # Handle rating distribution list
        key = str(key)  # Convert key to string for comparison
        for item in value:
            if str(item.get('rating')) == key:
                return item
    return {'count': 0} 