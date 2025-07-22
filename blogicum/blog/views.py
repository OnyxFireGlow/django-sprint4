from django.shortcuts import get_object_or_404, render

from .constants import INDEX_POSTS_COUNT
from .models import Category, Post


def index(request):
    """View для главной страницы - вывод последних публикаций."""
    # Используем кастомный менеджер published и берём нужное количество
    post_list = Post.published.select_related(
        'category', 'location', 'author'
    )[:INDEX_POSTS_COUNT]

    template = 'blog/index.html'
    context = {'post_list': post_list}
    return render(request, template, context)


def post_detail(request, post_id):
    """View для страницы отдельной публикации."""
    post = get_object_or_404(
        Post.published.select_related('category', 'location', 'author'),
        pk=post_id
    )

    template = 'blog/detail.html'
    context = {'post': post}
    return render(request, template, context)


def category_posts(request, category_slug):
    """View для страницы категории."""
    # Получаем категорию или 404 с проверкой is_published
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    # Используем кастомный менеджер published
    post_list = Post.published.filter(
        category=category
    ).select_related('location', 'author')

    template = 'blog/category.html'
    context = {
        'category': category,
        'post_list': post_list
    }
    return render(request, template, context)
