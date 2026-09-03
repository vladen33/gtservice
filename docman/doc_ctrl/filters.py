from django.db.models import Q
import django_filters
from .models import Doc, Person


class DocFilter(django_filters.FilterSet):
    """Фильтр для списка документов."""

    # Поиск по номеру ИЛИ наименованию (одна строка ввода)
    search = django_filters.CharFilter(
        method='filter_search',
        label='Поиск (номер или наименование)',
    )

    # Диапазон дат документа
    date_from = django_filters.DateFilter(
        field_name='date',
        lookup_expr='gte',
        label='Дата документа с',
    )
    date_to = django_filters.DateFilter(
        field_name='date',
        lookup_expr='lte',
        label='Дата документа по',
    )

    # Ответственное лицо (через связанную модель)
    person = django_filters.ModelChoiceFilter(
        field_name='responsibles__person',
        queryset=Person.objects.all().order_by('last_name', 'first_name'),
        label='Ответственный',
    )

    class Meta:
        model = Doc
        fields = ['status', 'doc_type']

    def filter_search(self, queryset, name, value):
        """Ищет совпадение в number ИЛИ title (регистронезависимо)."""
        return queryset.filter(
            Q(number__icontains=value)
            | Q(title__icontains=value)
        )