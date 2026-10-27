from decimal import Decimal, InvalidOperation

from django import template
from django.utils.html import format_html

register = template.Library()


def format_inr(value):
    """Format a number the Indian way: 1234567 -> ₹12,34,567."""
    try:
        number = int(Decimal(str(value)).quantize(Decimal("1")))
    except (InvalidOperation, TypeError, ValueError):
        return value
    digits = str(abs(number))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups) + "," + tail
    return f"{'-' if number < 0 else ''}₹{digits}"


@register.filter
def inr(value):
    return format_inr(value)


@register.simple_tag
def price(value, css_class="price"):
    """Price in INR, tagged so main.js can convert it to the chosen currency."""
    if value is None:
        return ""
    return format_html(
        '<span class="{}" data-price-inr="{}">{}</span>',
        css_class,
        int(Decimal(str(value))),
        format_inr(value),
    )
