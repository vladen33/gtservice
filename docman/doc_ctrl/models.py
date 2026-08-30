from datetime import datetime

from django.db import models
from django.utils import timezone

FIXED_DEFAULT_DATETIME = timezone.make_aware(datetime(9999, 1, 1))

class OrdStatus(models.TextChoices):
    ACTIVE = 'active', 'Действует'
    MODIFIED = 'modified', 'Изменён'
    CANCELLED = 'cancelled', 'Отменён'


class DocType(models.Model):
    type = models.CharField(
        max_length=127,
        verbose_name='Тип документа'
    )
    class Meta:
        verbose_name = 'Тип документа'
        verbose_name_plural = 'Типы документов'
    def __str__(self):
        return self.type


class Doc(models.Model):
    number = models.CharField(
        max_length=127,
        verbose_name='Номер документа'
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name='Дата документа'
    )
    doc_type = models.ForeignKey(
        'DocType',
        on_delete=models.RESTRICT,
        verbose_name='Тип документа'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Наименование документа'
    )
    summary = models.TextField(
        blank=True,
        null=True,
        verbose_name='Краткое содержание документа'
    )
    valid_from_date = models.DateField(
        default=timezone.now,
        verbose_name='Действует с'
    )
    valid_to_date = models.DateField(
        default=FIXED_DEFAULT_DATETIME,
        verbose_name='Действует до'
    )
    status = models.CharField(
        max_length=20,
        choices=OrdStatus,
        default=OrdStatus.ACTIVE,
        verbose_name='Статус документа'
    )

    created_at = models.DateTimeField(
        'Дата создания в системе',
        auto_now_add=True     # Автоматически ставит время создания записи в БД
    )
    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-date', 'number']

    def __str__(self):
        return f'{self.number} от {self.date}'


class Person(models.Model):
    last_name = models.CharField(
        max_length=63,
        verbose_name='Фамилия'
    )
    first_name = models.CharField(
        max_length=63,
        verbose_name='Имя'
    )
    middle_name = models.CharField(
        max_length=63,
        verbose_name='Отчество',
        blank=True,
        help_text='Можно оставить пустым, если отсутствует'
    )
    position = models.CharField(
        max_length=127,
        blank=True,
        help_text='Например: директор, главный бухгалтер',
        verbose_name = 'Должность'
    )

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name', 'middle_name']

    @property
    def full_name_initials(self):
        first = f'{self.first_name[0]}. ' if self.first_name else ''
        middle = f'{self.middle_name[0]}. ' if self.middle_name else ''
        return f'{self.last_name} {first}{middle}'.strip()

    def __str__(self):
        base = f'{self.last_name} {self.first_name}'
        if self.middle_name:
            base += f' {self.middle_name}'
        if self.position:
            base += f', {self.position}'
        return base

# Промежуточная модель для связи «Документ — ответственные»
class DocResponsible(models.Model):
    doc = models.ForeignKey(
        Doc,
        on_delete=models.CASCADE,
        related_name='responsibles',
        verbose_name='Документ',
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,  # PROTECT: нельзя удалить человека, если он назначен ответственным
        related_name='ords_as_responsible',
        verbose_name='Ответственное лицо',
    )
    role = models.CharField(
        max_length=127,
        blank=True,
        help_text='Например: ответственный исполнитель, контролёр, согласующий',
        verbose_name='Роль'
    )
    is_indefinite = models.BooleanField(
        default=False,
        verbose_name='Бессрочно'
    )
    deadline = models.DateField(
        null=True,
        blank=True,
        help_text='Если срок не ограничен — оставьте пустым',
        verbose_name='Срок исполнения'
    )
    task = models.TextField(
        blank=True,
        null=True,
        verbose_name='Поручение'
    )

    class Meta:
        verbose_name = 'Ответственный по документу'
        verbose_name_plural = 'Ответственные по документу'
        ordering = ['doc', 'person']

    def __str__(self):
        return f'{self.doc.number}: {self.person.full_name_initials} — {self.role}'
