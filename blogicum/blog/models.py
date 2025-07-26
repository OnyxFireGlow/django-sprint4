from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from core.constants import FIELD_LENGTHS
from core.models import NameModel, PublishedModel, TitleModel

User = get_user_model()


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
        default=timezone.now,
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        )
    )

    image = models.ImageField(
        'Изображение',
        upload_to='posts/',
        blank=True,
        null=True,
        help_text='Загрузите картинку'
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

    objects = models.Manager()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)
        default_related_name = 'posts'


class Comment(PublishedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Публикация'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        max_length=FIELD_LENGTHS['TEXT_AREA']
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Комментарий {self.author} к посту #{self.post.id}'
