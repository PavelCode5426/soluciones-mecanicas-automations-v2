from django.template import TemplateDoesNotExist
from django.template.loader import get_template

SYSTEM_MODULES = [
    {'app_name': 'facebook', 'label': 'Facebook', 'app_icon': 'ti ti-brand-facebook'},
    {'app_name': 'whatsapp', 'label': 'WhatsApp', 'app_icon': 'ti ti-brand-whatsapp'},
]


def system_modules(request):
    context = {}
    templates = []
    user = request.user

    if not user.is_anonymous:
        for module in SYSTEM_MODULES:
            module_name = module['app_name']
            try:
                sidebar_tab = f'layout/partials/left_sidebar_tabs/{module_name}.html'
                get_template(sidebar_tab)
            except TemplateDoesNotExist as e:
                sidebar_tab = f'layout/partials/left_sidebar_tabs/no_template.html'
            templates.append({
                'module_name': module_name,
                'sidebar_tab': sidebar_tab,
                'menu_id': f"menu-{module_name}",
                'tab_id': f"tab-{module_name}",
            })

        context.update({'SYSTEM_MODULES': SYSTEM_MODULES, 'MODULES_TEMPLATES': templates})
    return context
