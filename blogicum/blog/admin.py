from django.contrib import admin

from .models import Category, Location, Post, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Category.

    Настройки:
    - list_display: Отображаемые поля в списке объектов
    - list_editable: Поля, редактируемые прямо из списка
    - search_fields: Поля, по которым выполняется поиск
    - prepopulated_fields: Автозаполнение slug на основе title
    - list_filter: Фильтры для быстрой навигации
    """

    list_display = ('title', 'is_published', 'created_at')
    list_editable = ('is_published',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('is_published', 'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at', 'is_published')
    list_editable = ('is_published',)
    search_fields = ('text', 'author__username', 'post__title')
    list_filter = ('is_published', 'created_at')
    raw_id_fields = ('author', 'post')

    fieldsets = (
        (None, {
            'fields': ('post', 'author', 'text')
        }),
        ('Публикация', {
            'fields': ('is_published',)
        }),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Location.

    Особенности:
    - Минимальный набор настроек для простой модели
    - Быстрое включение/отключение публикации местоположения
    - Поиск по названию места

    Важно:
    - Удаление местоположения не удаляет связанные публикации
    - Неопубликованные местоположения не отображаются при создании постов
    """

    list_display = ('name', 'is_published', 'created_at')
    list_editable = ('is_published',)
    search_fields = ('name',)
    list_filter = ('is_published', 'created_at')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Post.

    Основные функции:
    - Управление публикациями с предпросмотром основных полей
    - Фильтрация по статусу, категории, местоположению и дате
    - Группировка полей в логические секции
    - Быстрое переключение статуса публикации

    Особенности:
    - date_hierarchy: Навигация по датам публикации
    - fieldsets: Логическая группировка полей формы редактирования

    Примеры использования:
    - Создание отложенных публикаций через поле pub_date
    - Массовое включение/выключение публикаций из списка
    - Поиск по заголовку и тексту публикаций
    """

    list_display = (
        'title',
        'pub_date',
        'is_published',
        'author',
        'location',
        'category',
        'created_at'
    )
    list_editable = ('is_published',)
    search_fields = ('title', 'text')
    list_filter = ('is_published', 'category', 'location', 'pub_date')
    date_hierarchy = 'pub_date'
    raw_id_fields = ('author',)

    # Автозаполнение полей
    fieldsets = (
        (None, {
            'fields': (
                'title',
                'text',
                'author',
                'location',
                'category'
            )
        }),
        ('Публикация', {
            'fields': (
                'is_published',
                'pub_date'
            )
        }),
    )
