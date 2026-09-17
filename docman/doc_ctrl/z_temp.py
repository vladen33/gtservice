

















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
            'files',
            Prefetch(
                'responsibles',
                queryset=DocResponsible.objects.select_related('person')
            ),
        )
    )

    # 4. Применяем фильтры
    doc_filter = DocFilter(request.GET, queryset=docs)

    # 5. Убираем дубликаты, если фильтр по person (JOIN даёт строки)
    filtered_qs = doc_filter.qs.distinct()

    context = {
        'docs': filtered_qs,
        'view_mode': view_mode,
        'filter': doc_filter,
    }
    return render(request, 'doc_ctrl/doc_list_base.html', context)