from django import template
register = template.Library()

@register.simple_tag(takes_context=True)
def switch_view_mode(context, mode):
    request = context['request']
    params = request.GET.copy()          # копируем текущие параметры
    params['view_mode'] = mode           # перезаписываем view_mode
    return f"?{params.urlencode()}"      # формируем итоговую строку