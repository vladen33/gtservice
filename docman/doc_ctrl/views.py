from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .forms import DocForm, DocResponsibleForm
from .models import Doc, DocResponsible, Person


# Create your views here.
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
    context = {
        'docs': docs,
        'view_mode': view_mode,  # передаём текущий режим в шаблон
    }
    return render(request, 'doc_ctrl/doc_list_base.html', context)


def doc_create(request):
    if request.method == 'POST':
        form = DocForm(request.POST)
        # Получаем списки данных из POST
        persons = request.POST.getlist('responsibles_person[]')
        roles = request.POST.getlist('responsibles_role[]')
        deadlines = request.POST.getlist('responsibles_deadline[]')
        tasks = request.POST.getlist('responsibles_tasks[]')

        # Проверяем, что длины списков совпадают
        n = len(persons)
        if not (len(roles) == n and len(deadlines) == n and len(tasks) == n):
            messages.error(request,
                           'Ошибка данных: количество полей не совпадает. Обновите страницу и попробуйте снова.')
            people = Person.objects.all()
            return render(request, 'doc_ctrl/doc_create.html', {'form': form, 'people': people})

        if form.is_valid():
            # Сохраняем документ
            doc_instance = form.save()

            # Сохраняем ответственных в цикле
            for i in range(n):
                person_id = persons[i]
                if not person_id:
                    continue  # пропускаем пустые строки, если они есть
                role = roles[i].strip()
                if deadlines[i] == '':
                    is_indefinite = True
                    deadline = None
                else:
                    is_indefinite = False
                    deadline = deadlines[i]
                task = tasks[i].strip() or None

                resp_form = DocResponsibleForm({
                    'person': person_id,
                    'role': role,
                    'is_indefinite': is_indefinite,
                    'deadline': deadline,
                    'task': task,
                })

                if resp_form.is_valid():
                    resp_instance = resp_form.save(commit=False)
                    resp_instance.doc = doc_instance
                    resp_instance.save()
                else:
                    # Если хоть одна строка невалидна — откатываем всё
                    messages.error(request, f'Ошибка при сохранении ответственного #{i + 1}: {resp_form.errors}')
                    doc_instance.delete()  # удаляем документ, если не удалось сохранить все связи
                    people = Person.objects.all()
                    return render(request, 'doc_ctrl/doc_create.html', {'form': form, 'people': people})

            messages.success(request, 'Документ и ответственные успешно сохранены.')
            return redirect('doc_ctrl:doc_list')
        else:
            people = Person.objects.all()
            return render(request, 'doc_ctrl/doc_create.html', {'form': form, 'people': people})
    else:
        form = DocForm()
        people = Person.objects.all()
        return render(request, 'doc_ctrl/doc_create.html', {'form': form, 'people': people})


def doc_detail(request, pk):
    instance = get_object_or_404(Doc, pk=pk)
    template_name = 'doc_ctrl/doc_detail.html'
    context = {'instance': instance}
    return render(request, template_name, context)


def doc_edit(request, pk):
    doc_instance = get_object_or_404(Doc, pk=pk)
    people = Person.objects.all().order_by('last_name', 'first_name', 'middle_name')
    responsibles = (
        DocResponsible.objects
        .filter(doc=doc_instance)
        .select_related('person')
        .order_by('role', 'person__last_name')
    )

    if request.method == 'POST':
        form = DocForm(request.POST, instance=doc_instance)

        # Получаем списки данных из POST
        persons = request.POST.getlist('responsibles_person[]')
        roles = request.POST.getlist('responsibles_role[]')
        deadlines = request.POST.getlist('responsibles_deadline[]')
        tasks = request.POST.getlist('responsibles_task[]')

        n = len(persons)
        if not (len(roles) == n and len(deadlines) == n and len(tasks) == n):
            messages.error(request, 'Ошибка данных: количество полей не совпадает. Обновите страницу и попробуйте снова.')
            return render(request, 'doc_ctrl/doc_edit.html', {
                'form': form,
                'people': people,
                'responsibles': responsibles,
            })

        if form.is_valid():
            # 1) Сохраняем основной документ
            doc_instance = form.save()

            # 2) Удаляем все текущие связи (перезапись)
            DocResponsible.objects.filter(doc=doc_instance).delete()

            # 3) Создаём заново из POST-данных
            for i in range(n):
                person_id = persons[i]
                if not person_id:
                    continue

                role = roles[i].strip()
                if deadlines[i] == '':
                    is_indefinite = True
                    deadline = None
                else:
                    is_indefinite = False
                    deadline = deadlines[i]
                task = tasks[i].strip() or None

                resp_form = DocResponsibleForm({
                    'person': person_id,
                    'role': role,
                    'is_indefinite': is_indefinite,
                    'deadline': deadline,
                    'task': task,
                })

                if resp_form.is_valid():
                    resp_instance = resp_form.save(commit=False)
                    resp_instance.ord = doc_instance
                    resp_instance.save()
                else:
                    messages.error(request, f'Ошибка при сохранении ответственного #{i + 1}: {resp_form.errors}')
                    # Откат: удаляем созданные строки и сам документ (если нужно)
                    # OrdResponsible.objects.filter(ord=ord_instance).delete()
                    return render(request, 'doc_ctrl/doc_edit.html', {
                        'form': form,
                        'people': people,
                        'responsibles': responsibles,
                    })

            messages.success(request, 'Документ и ответственные успешно обновлены.')
            return redirect('doc_ctrl:doc_list')
        else:
            # Форма DocForm невалидна: показываем ошибки
            return render(request, 'doc_ctrl/doc_edit.html', {
                'form': form,
                'people': people,
                'responsibles': responsibles,
            })
    else:
        form = DocForm(instance=doc_instance)

    return render(request, 'doc_ctrl/doc_edit.html', {
        'form': form,
        'people': people,
        'responsibles': responsibles,
    })


def doc_delete(request, pk):
    instance = get_object_or_404(Doc, pk=pk)
    if request.method == 'POST':
        instance.delete()
        return redirect('doc_ctrl:ord_list')

    # Для GET-запроса показываем страницу подтверждения
    context = {
        'instance': instance
    }
    return render(request, 'doc_ctrl/doc_delete.html', context)