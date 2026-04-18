from django import template

register = template.Library()


@register.filter
def split(value, delimiter=" "):
    """
    Divide un string usando el delimitador dado.
    Uso: {{ value|split:"," }}
    """
    if value:
        return value.split(delimiter)
    return []


@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return ''


@register.filter
def parse_whatsapp_chat(value, use_plus=True):
    phone = value.split('@')[0]
    if not use_plus:
        return phone
    return f"+{phone[:2]} {phone[2:]}"
