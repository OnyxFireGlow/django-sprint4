from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (PasswordChangeView,
                                       PasswordChangeDoneView)
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, UpdateView

from .constants import POSTS_PER_PAGE
from .forms import CommentForm, PostForm, SignUpForm
from .models import Category, Comment, Post

User = get_user_model()


class BasePostAccessMixin(UserPassesTestMixin):
    """Mixin для проверки прав доступа к операциям с постами."""

    def test_func(self):
        """Проверяет, является ли пользователь автором поста."""
        if not self.request.user.is_authenticated:
            return False
        return self.request.user == self.get_object().author

    def handle_no_permission(self):
        """Перенаправляет на страницу поста при отсутствии прав."""
        post_id = self.kwargs.get('post_id')
        return redirect('blog:post_detail', post_id=post_id)


@login_required
def profile_redirect(request):
    """Перенаправляет аутентифицированного пользователя на его профиль."""
    return redirect('blog:profile', username=request.user.username)


@require_http_methods(["POST"])
def custom_logout(request):
    """Обрабатывает выход пользователя с защитой от CSRF."""
    logout(request)
    return redirect('blog:index')


def index(request):
    """
    Отображает главную страницу с последними опубликованными постами.

    Использует пагинацию с количеством постов на странице из константы.
    """
    now = timezone.now()
    post_list = Post.objects.filter(
        is_published=True,
        pub_date__lte=now,
        category__is_published=True
    ).annotate(
        comment_count=Count('comments')
    ).select_related(
        'category', 'location', 'author'
    ).order_by('-pub_date')

    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    """
    Отображает детальную страницу поста.

    Проверяет права доступа:
    - Автор видит пост в любом статусе
    - Остальные пользователи видят только опубликованные посты
    """
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        pk=post_id
    )

    now = timezone.now()
    if not (request.user == post.author or (
        post.is_published
        and post.pub_date <= now
        and (not post.category or post.category.is_published)
    )):
        raise Http404("Пост не доступен")

    comments = post.comments.select_related('author').order_by('created_at')
    form = CommentForm() if request.user.is_authenticated else None

    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


def category_posts(request, category_slug):
    """
    Отображает посты в указанной категории.

    Категория должна быть опубликована, \
        посты проходят стандартную проверку видимости.
    """
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    now = timezone.now()
    post_list = Post.objects.filter(
        is_published=True,
        pub_date__lte=now,
        category=category
    ).annotate(
        comment_count=Count('comments')
    ).select_related('location', 'author').order_by('-pub_date')

    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj
    })


class PostCreateView(LoginRequiredMixin, CreateView):
    """View для создания нового поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Устанавливает автора поста перед сохранением."""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Перенаправляет в профиль автора после создания."""
        return reverse('blog:profile', args=[self.request.user.username])


class PostUpdateView(BasePostAccessMixin, UpdateView):
    """View для редактирования существующего поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        """Перенаправляет на страницу поста после редактирования."""
        return reverse('blog:post_detail', args=[self.object.id])


class PostDeleteView(BasePostAccessMixin, DeleteView):
    """View для удаления поста."""

    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        """Добавляет пост в контекст для подтверждения удаления."""
        context = super().get_context_data(**kwargs)
        context['post'] = self.object
        return context


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    now = timezone.now()

    post_list = Post.objects.filter(author=profile_user).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

    if request.user != profile_user:
        post_list = post_list.filter(
            is_published=True,
            pub_date__lte=now,
            category__is_published=True
        )

    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile_user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View для редактирования профиля пользователя."""

    model = User
    fields = ['first_name', 'last_name', 'username', 'email']
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:profile_redirect')

    def get_object(self, queryset=None):
        """Возвращает текущего аутентифицированного пользователя."""
        return self.request.user

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы в контекст."""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование профиля - {self.request.
                                                       user.username}'
        return context


@login_required
def add_comment(request, post_id):
    """
    Обрабатывает добавление комментария к посту.

    Проверяет:
    - Доступность поста для текущего пользователя
    - Авторизацию пользователя
    """
    post = get_object_or_404(Post, pk=post_id)
    now = timezone.now()

    # Проверка видимости поста для неавторов
    if request.user != post.author and (
        not post.is_published
        or post.pub_date > now
        or (post.category and not post.category.is_published)
    ):
        raise Http404("Пост не доступен")

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm()

    comments = post.comments.select_related('author').order_by('created_at')
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


@login_required
def edit_comment(request, post_id, comment_id):
    """Обрабатывает редактирование существующего комментария."""
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        author=request.user,
        post_id=post_id
    )

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, post_id, comment_id):
    """Обрабатывает удаление комментария, включая подтверждение через GET."""
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        author=request.user,
        post_id=post_id
    )

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Комментарий успешно удалён')
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment,
    })


class SignUpView(CreateView):
    """View для регистрации новых пользователей."""

    form_class = SignUpForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Кастомный View для изменения пароля."""

    success_url = reverse_lazy('blog:password_change_done')

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы в контекст."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Изменение пароля'
        return context


class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    """View для отображения успешного изменения пароля."""

    def get_context_data(self, **kwargs):
        """Добавляет флаг успешного изменения пароля в контекст."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Пароль успешно изменён'
        context['password_changed'] = True
        return context
