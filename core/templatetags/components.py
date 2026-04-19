from django import template
from django.middleware.csrf import get_token
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def status_badge(valor, texto_activo="Activo", texto_inactivo="Inactivo"):
    if valor:
        html = f'<span class="badge bg-success">{texto_activo}</span>'
    else:
        html = f'<span class="badge bg-danger">{texto_inactivo}</span>'
    return mark_safe(html)


@register.simple_tag(takes_context=True)
def toggle_status_badge(context, valor, submit_url, texto_activo="Activo", texto_inactivo="Inactivo"):
    request = context['request']
    csrf_token = get_token(request)
    csrf_input = f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'

    if valor:
        submit = f'<input type="submit" class="btn btn-xs btn-success" value="{texto_activo}"/>'
    else:
        submit = f'<input type="submit" class="btn btn-xs btn-danger" value="{texto_inactivo}"/>'

    return mark_safe('<form method="post" action="{}">{}{}</form>'.format(submit_url, submit, csrf_input))


@register.simple_tag
def object_link(account, url):
    url = reverse_lazy(url, kwargs={"pk": account.pk})
    return mark_safe('<a class="btn" href="{}">{}</a>'.format(url, account))
