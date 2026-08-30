from django.contrib import admin
from .models import Doc, Person, DocType, DocResponsible
from .forms import (
    DocForm,
    # OrdCancellationForm,
    DocResponsibleForm
)


# --- Inline для ответственных (OrdResponsible) ---
class DocResponsibleInline(admin.TabularInline):
    model = DocResponsible
    form = DocResponsibleForm
    extra = 1
    verbose_name = 'Ответственный'
    verbose_name_plural = 'Ответственные'
    raw_id_fields = ('person',)
    ordering = ['role', 'person__last_name']

@admin.register(Doc)
class OrdAdmin(admin.ModelAdmin):
    form = DocForm
    list_display = (
        'number',
        'date',
        'doc_type',
        'title',
        'status',
        'valid_from_date',
    )
    list_filter = (
        'doc_type',
        'date',
        'status',
    )
    search_fields = (
        'number',
        'title',
        'summary',
    )
    date_hierarchy = 'date'

    inlines = [
        DocResponsibleInline,
    ]

    fieldsets = (
        ('Основное', {
            'fields': ('number', 'date', 'doc_type', 'title'),
        }),
        ('Содержание и статус', {
            'fields': ('summary', 'status'),
        }),
        ('Период действия', {
            'fields': ('valid_from_date', 'valid_to_date'),
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('created_at',)
    list_per_page = 100



@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'position')
    search_fields = ('last_name', 'first_name', 'middle_name')
    list_filter = ('position',)
    ordering = ('last_name', 'first_name')


@admin.register(DocType)
class OrdTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(DocResponsible)
class DocResponsibleAdmin(admin.ModelAdmin):
    list_display = ('doc', 'person', 'role', 'deadline')
    list_filter = ('role', 'deadline')
    search_fields = ('doc__number', 'person__last_name')
    raw_id_fields = ('doc', 'person')
