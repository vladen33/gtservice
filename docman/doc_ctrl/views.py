import logging

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .filters import DocFilter
from .forms import DocForm, DocResponsibleForm
from .models import Doc, DocResponsible, Person


logger = logging.getLogger(__name__)

def doc_list(request):
    # 1. Получаем выбор пользователя из сессии; по умолчанию — 'table'
    view_mode = request.session.get('ord_view_mode', 'table')

    # 2. Если пользователь явно сменил режим через GET-параметр, обновляем сессию
    new_mode = request.GET.get('view_mode')
    if new_mode in ['table', 'cards']:
        view_mode = new_mode
        request.session['ord_view_mode'] = view_mode

    # 3. Подготавливаем данные (с prefetch_related для производительности)
    docs = (
        Doc.objects
        .select_related('doc_type')
        .prefetch_related(
            Prefetch(
                'responsibles',
                queryset=DocResponsible.objects.select_related('person')
            )
        )
    )

    # 3. Применяем фильтры
    doc_filter = DocFilter(request.GET, queryset=docs)

    # 4. Убираем дубликаты, если фильтр по person (JOIN даёт строки)
    filtered_qs = doc_filter.qs.distinct()


    context = {
        'docs': docs,
        'view_mode': view_mode,  # передаём текущий режим в шаблон
        'filter': doc_filter,
    }
    return render(request, 'doc_ctrl/doc_list_base.html', context)


def doc_detail(request, pk):
    doc = get_object_or_404(Doc, pk=pk)
    responsibles = (
        doc.responsibles
        .select_related('person')
        .order_by('role', 'person__last_name')
    )
    return render(request, 'doc_ctrl/doc_detail.html', {
        'doc': doc,
        'responsibles': responsibles,
    })


def doc_delete(request, pk):
    instance = get_object_or_404(Doc, pk=pk)
    if request.method == 'POST':
        instance.delete()
        return redirect('doc_ctrl:doc_list')

    # Для GET-запроса показываем страницу подтверждения
    context = {
        'instance': instance
    }
    return render(request, 'doc_ctrl/doc_delete.html', {'instance': instance})


def doc_create_or_edit(request, pk=None):
    is_edit = bool(pk)
    doc_instance = None
    people = Person.objects.all().order_by('last_name', 'first_name', 'middle_name')
    responsibles = []

    if is_edit:
        doc_instance = get_object_or_404(Doc, pk=pk)
        responsibles = (
            DocResponsible.objects
            .filter(doc=doc_instance)
            .select_related('person')
            .order_by('role', 'person__last_name')
        )

    if request.method == 'POST':
        logger.info('--- %s документа ---', 'Редактирование' if is_edit else 'Создание')
        logger.info('ID = %s, метод = %s', pk or 'новый', request.method)

        form = DocForm(request.POST, instance=doc_instance)

        persons = request.POST.getlist('responsibles_person[]')
        roles = request.POST.getlist('responsibles_role[]')
        deadlines = request.POST.getlist('responsibles_deadline[]')
        tasks = request.POST.getlist('responsibles_task[]')

        n = len(persons)
        if not (len(roles) == n and len(deadlines) == n and len(tasks) == n):
            logger.error("Ошибка данных: количество полей не совпадает.")
            messages.error(request, "Ошибка данных: количество полей не совпадает.")
            return redirect('doc_ctrl:doc_list')

        if not form.is_valid():
            logger.error('Форма DocForm невалидна')
            return render(request, 'doc_ctrl/doc_form.html', {
                'form': form,
                'people': people,
                'is_edit': is_edit,
                'responsibles': responsibles,
            })

        try:
            with transaction.atomic():
                doc_instance = form.save()
                DocResponsible.objects.filter(doc=doc_instance).delete()

                for i in range(n):
                    person_id = persons[i]
                    if not person_id:
                        continue

                    deadline = deadlines[i] or None
                    is_indefinite = deadline is None

                    resp_form = DocResponsibleForm({
                        'person': person_id,
                        'role': roles[i].strip(),
                        'is_indefinite': is_indefinite,
                        'deadline': deadline,
                        'task': tasks[i].strip() or None,
                    })

                    if not resp_form.is_valid():
                        logger.error(
                            'Ошибка в строке #%d: %s',
                            i + 1, resp_form.errors.as_text(),
                        )
                        raise ValueError(f'Ошибка в строке {i + 1}')

                    resp_instance = resp_form.save(commit=False)
                    resp_instance.doc = doc_instance
                    resp_instance.save()

        except ValueError:
            messages.error(
                request,
                'Ошибка при сохранении ответственных. Проверьте введённые данные.'
            )
            return render(request, 'doc_ctrl/doc_form.html', {
                'form': form,
                'people': people,
                'is_edit': is_edit,
                'responsibles': responsibles,
            })

        messages.success(
            request,
            'Документ успешно обновлён.' if is_edit else 'Документ успешно создан.'
        )
        return redirect('doc_ctrl:doc_list')

    # GET
    form = DocForm(instance=doc_instance)
    return render(request, 'doc_ctrl/doc_form.html', {
        'form': form,
        'people': people,
        'is_edit': is_edit,
        'responsibles': responsibles,
    })
