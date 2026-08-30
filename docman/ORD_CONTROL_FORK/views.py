from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .forms import OrdForm, OrdResponsibleForm
from .models import Ord, OrdResponsible, Person


# Create your views here.
def ord_list(request):
    # 1. Получаем выбор пользователя из сессии; по умолчанию — 'table'
    view_mode = request.session.get('ord_view_mode', 'table')

    # 2. Если пользователь явно сменил режим через GET-параметр, обновляем сессию
    new_mode = request.GET.get('view_mode')
    if new_mode in ['table', 'cards']:
        view_mode = new_mode
        request.session['ord_view_mode'] = view_mode

    # 3. Подготавливаем данные (с prefetch_related для производительности)
    ords = (
        Ord.objects
        .select_related('ord_type')
        .prefetch_related(
            Prefetch(
                'responsibles',
                queryset=OrdResponsible.objects.select_related('person')
            )
        )
    )
    context = {
        'ords': ords,
        'view_mode': view_mode,  # передаём текущий режим в шаблон
    }
    return render(request, 'ordcontrol/ord_list.html', context)


def ord_create(request):
    if request.method == 'POST':
        form = OrdForm(request.POST)
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
            return render(request, 'ordcontrol/ord_create.html', {'form': form, 'people': people})

        if form.is_valid():
            # Сохраняем документ
            ord_instance = form.save()

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

                resp_form = OrdResponsibleForm({
                    'person': person_id,
                    'role': role,
                    'is_indefinite': is_indefinite,
                    'deadline': deadline,
                    'task': task,
                })

                if resp_form.is_valid():
                    resp_instance = resp_form.save(commit=False)
                    resp_instance.ord = ord_instance
                    resp_instance.save()
                else:
                    # Если хоть одна строка невалидна — откатываем всё
                    messages.error(request, f'Ошибка при сохранении ответственного #{i + 1}: {resp_form.errors}')
                    ord_instance.delete()  # удаляем документ, если не удалось сохранить все связи
                    people = Person.objects.all()
                    return render(request, 'ordcontrol/ord_create.html', {'form': form, 'people': people})

            messages.success(request, 'Документ и ответственные успешно сохранены.')
            return redirect('ordcontrol:ord_list')
        else:
            people = Person.objects.all()
            return render(request, 'ordcontrol/ord_create.html', {'form': form, 'people': people})
    else:
        form = OrdForm()
        people = Person.objects.all()
        return render(request, 'ordcontrol/ord_create.html', {'form': form, 'people': people})


def ord_detail(request, pk):
    instance = get_object_or_404(Ord, pk=pk)
    template_name = 'ordcontrol/ord_detail.html'
    context = {'instance': instance}
    return render(request, template_name, context)


def ord_edit(request, pk):
    ord_instance = get_object_or_404(Ord, pk=pk)
    people = Person.objects.all().order_by('last_name', 'first_name', 'middle_name')
    responsibles = (
        OrdResponsible.objects
        .filter(ord=ord_instance)
        .select_related('person')
        .order_by('role', 'person__last_name')
    )

    if request.method == 'POST':
        form = OrdForm(request.POST, instance=ord_instance)

        # Получаем списки данных из POST
        persons = request.POST.getlist('responsibles_person[]')
        roles = request.POST.getlist('responsibles_role[]')
        deadlines = request.POST.getlist('responsibles_deadline[]')
        tasks = request.POST.getlist('responsibles_task[]')

        n = len(persons)
        if not (len(roles) == n and len(deadlines) == n and len(tasks) == n):
            messages.error(request, 'Ошибка данных: количество полей не совпадает. Обновите страницу и попробуйте снова.')
            return render(request, 'ordcontrol/ord_edit.html', {
                'form': form,
                'people': people,
                'responsibles': responsibles,
            })

        if form.is_valid():
            # 1) Сохраняем основной документ
            ord_instance = form.save()

            # 2) Удаляем все текущие связи (перезапись)
            OrdResponsible.objects.filter(ord=ord_instance).delete()

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

                resp_form = OrdResponsibleForm({
                    'person': person_id,
                    'role': role,
                    'is_indefinite': is_indefinite,
                    'deadline': deadline,
                    'task': task,
                })

                if resp_form.is_valid():
                    resp_instance = resp_form.save(commit=False)
                    resp_instance.ord = ord_instance
                    resp_instance.save()
                else:
                    messages.error(request, f'Ошибка при сохранении ответственного #{i + 1}: {resp_form.errors}')
                    # Откат: удаляем созданные строки и сам документ (если нужно)
                    # OrdResponsible.objects.filter(ord=ord_instance).delete()
                    return render(request, 'ordcontrol/ord_edit.html', {
                        'form': form,
                        'people': people,
                        'responsibles': responsibles,
                    })

            messages.success(request, 'Документ и ответственные успешно обновлены.')
            return redirect('ordcontrol:ord_list')
        else:
            # Форма OrdForm невалидна: показываем ошибки
            return render(request, 'ordcontrol/ord_edit.html', {
                'form': form,
                'people': people,
                'responsibles': responsibles,
            })
    else:
        form = OrdForm(instance=ord_instance)

    return render(request, 'ordcontrol/ord_edit.html', {
        'form': form,
        'people': people,
        'responsibles': responsibles,
    })


def ord_delete(request, pk):
    instance = get_object_or_404(Ord, pk=pk)
    if request.method == 'POST':
        instance.delete()
        return redirect('ordcontrol:ord_list')

    # Для GET-запроса показываем страницу подтверждения
    context = {
        'instance': instance
    }
    return render(request, 'ordcontrol/ord_delete.html', context)