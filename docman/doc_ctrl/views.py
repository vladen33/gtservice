import logging
import os

from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
from .filters import DocFilter
from .forms import DocForm, DocResponsibleForm
from .models import Doc, DocFile, DocResponsible, Person


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
        # 'docs': docs,
        # 'view_mode': view_mode,  # передаём текущий режим в шаблон
        # 'filter': doc_filter,
        'docs': filtered_qs,
        'view_mode': view_mode,
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
    return render(request, 'doc_ctrl/doc_delete.html', {'instance': instance})


def doc_create_or_edit(request, pk=None):
    is_edit = bool(pk)
    doc_instance = None
    people = Person.objects.all().order_by('last_name', 'first_name', 'middle_name')
    responsibles = []
    existing_files = []

    if is_edit:
        doc_instance = get_object_or_404(Doc, pk=pk)
        responsibles = (
            DocResponsible.objects
            .filter(doc=doc_instance)
            .select_related('person')
            .order_by('role', 'person__last_name')
        )
        existing_files = doc_instance.files.all()

    if request.method == 'POST':
        logger.info('--- %s документа ---', 'Редактирование' if is_edit else 'Создание')
        logger.info('ID = %s, метод = %s', pk or 'новый', request.method)

        # request.FILES обязателен — без него файлы не попадут в обработку
        form = DocForm(request.POST, request.FILES, instance=doc_instance)

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
                'existing_files': existing_files,
                'doc': doc_instance,
            })

        # Получаем список загруженных файлов из request.FILES
        uploaded_files = request.FILES.getlist('files')
        logger.info('Получено файлов: %d', len(uploaded_files))

        # Валидация файлов ДО входа в транзакцию
        file_errors = []

        for f in uploaded_files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                message = f'«{f.name}»: недопустимый формат {ext}. Разрешены только PDF и DOCX.'
                logger.error(message)
                file_errors.append(message)
            if f.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                message = f'«{f.name}»: превышен максимальный размер ({MAX_FILE_SIZE_MB} МБ).'
                logger.error(message)
                file_errors.append(message)

        if file_errors:
            for err in file_errors:
                messages.error(request, err)
            return render(request, 'doc_ctrl/doc_form.html', {
                'form': form,
                'people': people,
                'is_edit': is_edit,
                'responsibles': responsibles,
                'existing_files': existing_files,
                'doc': doc_instance,
            })

        try:
            with transaction.atomic():
                doc_instance = form.save()
                # При сохранении документа все ответственные удаляются и добавляются заново
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

                # --- Файлы ---
                # Сохраняем только если файлы реально загружены.
                # doc_instance уже имеет pk, поэтому doc_file_path
                # сработает корректно.
                for f in uploaded_files:
                    DocFile.objects.create(
                        doc=doc_instance,
                        file=f,
                        original_name=f.name,
                    )
                    logger.info('Сохранён файл: %s', f.name)

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
                'existing_files': existing_files,
                'doc': doc_instance,
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
        'existing_files': existing_files,
        'doc': doc_instance,
    })


def doc_file_download(request, pk, file_pk):
    """Скачивание файла документа."""
    doc_file = get_object_or_404(DocFile, pk=file_pk, doc_id=pk)

    if not doc_file.file:
        logger.error('Файл не найден на диске: DocFile #%s', file_pk)
        raise Http404('Файл не найден')

    # Открываем файл как поток, чтобы не грузить целиком в память
    response = FileResponse(
        doc_file.file.open('rb'),
        as_attachment=True,
        filename=doc_file.original_name,
    )
    return response


def doc_file_delete(request, pk, file_pk):
    """Удаление файла документа (запись в БД + файл с диска)."""
    doc_file = get_object_or_404(DocFile, pk=file_pk, doc_id=pk)

    if request.method == 'POST':
        filename = doc_file.original_name
        # Удаляем файл с диска
        if doc_file.file:
            doc_file.file.delete(save=False)
        # Удаляем запись из БД
        doc_file.delete()

        logger.info('Удалён файл «%s» из документа #%s', filename, pk)
        messages.success(request, f'Файл «{filename}» удалён.')
        return redirect('doc_ctrl:doc_edit', pk=pk)

    logger.warning('Попытка удаления файла через GET — запрещено')
    messages.error(request, 'Удаление файла возможно только через POST-запрос.')
    return redirect('doc_ctrl:doc_edit', pk=pk)