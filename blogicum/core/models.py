from django.db import models

from .constants import FIELD_LENGTHS


class PublishedModel(models.Model):
    """Абстрактная модель для публикуемых объектов."""

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        abstract = True


class TitleModel(models.Model):
    """Миксин для моделей с заголовком."""

    title = models.CharField(
        'Заголовок',
        max_length=FIELD_LENGTHS['TITLE'],
        help_text='Основной заголовок объекта.'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class NameModel(models.Model):
    """Миксин для моделей с названием."""

    name = models.CharField(
        'Название',
        max_length=FIELD_LENGTHS['TITLE'],
        help_text='Уникальное название объекта.'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
