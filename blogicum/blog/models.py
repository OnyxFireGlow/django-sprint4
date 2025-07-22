from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import PublishedModel, TitleModel, NameModel
from core.constants import FIELD_LENGTHS

User = get_user_model()


class PublishedPostManager(models.Manager):
    """
    Кастомный менеджер для работы с опубликованными постами.

    Предоставляет методы для получения только тех постов, которые:
    - Имеют статус опубликовано (is_published=True)
    - Имеют дату публикации не позже текущего времени
    - Принадлежат опубликованной категории
    """

    def get_queryset(self):
        """Возвращает базовый QuerySet с примененными фильтрами публикации."""
        current_time = timezone.now()
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lte=current_time,
            category__is_published=True
        )


class Category(PublishedModel, TitleModel):
    """Тематическая категория для публикаций."""

    description = models.TextField(
        verbose_name='Описание',
        help_text='Полное описание категории.'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        max_length=FIELD_LENGTHS['SLUG'],
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('title',)


class Location(PublishedModel, NameModel):
    """Географическая метка для публикаций."""

    name = models.CharField(
        'Название места',
        max_length=FIELD_LENGTHS['TITLE'],
        help_text='Географическое название.'
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ('name',)


class Post(PublishedModel, TitleModel):
    """Публикация в блоге."""

    text = models.TextField(
        verbose_name='Текст',
        help_text='Основное содержание публикации.'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )

    objects = models.Manager()  # Стандартный менеджер
    '''Кастомный менеджер для опубликованных постов'''
    published = PublishedPostManager()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)
        default_related_name = 'posts'
