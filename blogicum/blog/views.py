from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordChangeDoneView,
)
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, UpdateView

from .constants import POSTS_PER_PAGE
from .forms import CommentForm, PostForm, SignUpForm
from .models import Category, Comment, Post

User = get_user_model()


class BasePostAccessMixin(UserPassesTestMixin):
    """Базовый миксин для проверки доступа к постам"""

    def test_func(self):
        """Проверяем, является ли пользователь автором поста"""
        if not self.request.user.is_authenticated:
            return False
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        """Перенаправляем всех пользователей без прав на страницу поста"""
        post_id = self.kwargs.get('post_id')
        return redirect('blog:post_detail', post_id=post_id)


@login_required
def profile_redirect(request):
    """Перенаправление на профиль текущего пользователя"""
    return redirect('blog:profile', username=request.user.username)


@require_http_methods(["POST"])
def custom_logout(request):
    """Кастомный выход из системы через GET-запрос с отключенной CSRF-защитой"""
    logout(request)
    return redirect('blog:index')


def index(request):
    """View для главной страницы - вывод последних публикаций."""
    now = timezone.now()

    # Получаем QuerySet опубликованных постов (без get_object_or_404)
    post_list = Post.objects.filter(
        is_published=True,
        pub_date__lte=now,
        category__is_published=True
    ).annotate(
        comment_count=Count('comments')
    ).select_related(
        'category', 'location', 'author'
    ).order_by('-pub_date',)

    # Пагинация
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    """View для страницы отдельной публикации."""
    now = timezone.now()

    # Получаем пост без фильтрации
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        pk=post_id
    )

    # Проверяем права доступа
    if request.user != post.author:  # Если пользователь не автор
        # Проверяем условия видимости поста
        if not post.is_published or post.pub_date > now or (post.category and not post.category.is_published):
            raise Http404("Пост не доступен")

    comments = post.comments.all().order_by('created_at')
    form = CommentForm() if request.user.is_authenticated else None

    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


def category_posts(request, category_slug):
    """View для страницы категории."""
    # Получаем категорию или 404 с проверкой is_published
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
    ).select_related('location', 'author').order_by('-pub_date',)

    # Добавляем пагинацию
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj  # Передаем page_obj вместо posts
    }
    return render(request, 'blog/category.html', context)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostUpdateView(BasePostAccessMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.object.id])


class PostDeleteView(BasePostAccessMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.object
        return context


@login_required
def profile(request, username):
    print(f"DEBUG: Starting profile view for {username}")
    profile_user = get_object_or_404(User, username=username)
    print(f"DEBUG: Found user: {profile_user}")

    now = timezone.now()
    print(f"DEBUG: Time now: {now}")

    try:

        # Получаем все посты пользователя
        post_list = Post.objects.filter(author=profile_user).annotate(
            comment_count=Count('comments')
        ).select_related('category', 'location').order_by('-pub_date',)

        # Разделяем посты для автора и других пользователей
        if request.user == profile_user:
            # Автор видит все свои посты (включая отложенные и неопубликованные)
            visible_posts = post_list
        else:
            # Остальные видят только опубликованные с подошедшей датой
            visible_posts = post_list.filter(
                is_published=True,
                pub_date__lte=now
            ).order_by('-pub_date',)

        # Пагинация
        paginator = Paginator(visible_posts, POSTS_PER_PAGE)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'profile': profile_user,
            'page_obj': page_obj,
            'first_name': profile_user.first_name or "",
            'last_name': profile_user.last_name or "",
        }
        print(f"DEBUG: Context: {context}")
        response = render(request, 'blog/profile.html', context)
        print(f"DEBUG: Response content length: {len(response.content)}")
        return response
    except Exception as e:
        print(f"ERROR in profile view: {str(e)}")
        raise


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'username', 'email']
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:profile_redirect')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование \
            профиля - {self.request.user.username}'
        return context


@login_required
def add_comment(request, post_id):
    # Получаем пост или 404
    post = get_object_or_404(Post, pk=post_id)

    # Проверяем доступность поста
    if request.user != post.author:
        now = timezone.now()
        if (not post.is_published or post.pub_date > now
                or (post.category and not post.category.is_published)):
            raise Http404("Пост не доступен")

    # Только для POST-запросов
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.is_published = True
            comment.save()
            # Редирект после успешного сохранения
            return redirect('blog:post_detail', post_id=post_id)
    else:
        # Для GET-запросов просто показываем форму
        form = CommentForm()

    # Если форма невалидна, показываем страницу с ошибками
    comments = post.comments.all().order_by('created_at')
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


@login_required
def edit_comment(request, post_id, comment_id):
    # Получаем комментарий или 404
    comment = get_object_or_404(Comment, id=comment_id)

    # Проверяем права доступа
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)

    # Только для POST-запросов
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            # Редирект после успешного сохранения
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    # Если форма невалидна, показываем страницу с ошибками
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
        'post_id': post_id
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Комментарий успешно удалён')
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post_id': post_id
    })


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy('blog:password_change_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Изменение пароля'
        return context


class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Пароль успешно изменён'
        context['password_changed'] = True
        return context
