# recipes/templatetags/recipe_tags.py
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def url_transform(context, **kwargs):
    """
    Создает URL-строку с обновленными GET-параметрами.
    Сохраняет все текущие параметры и добавляет/изменяет те, что переданы в тег.
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()


@register.filter
def get_item(dictionary, key):
    """ Позволяет получать значение из словаря по ключу в шаблоне. """
    return dictionary.get(key)