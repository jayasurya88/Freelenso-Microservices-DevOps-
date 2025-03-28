from django import template

register = template.Library()

@register.filter
def get_item(rating_distribution, rating):
    """Get rating count from rating distribution"""
    rating = str(rating)  # Convert rating to string for comparison
    for item in rating_distribution:
        if str(item.get('rating')) == rating:
            return item
    return {'count': 0} 