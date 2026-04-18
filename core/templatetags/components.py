from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def status_badge(valor, texto_activo="Activo", texto_inactivo="Inactivo"):
    if valor:
        html = f'<span class="badge bg-success">{texto_activo}</span>'
    else:
        html = f'<span class="badge bg-danger">{texto_inactivo}</span>'
    return mark_safe(html)
