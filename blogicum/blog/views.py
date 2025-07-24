from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.views import PasswordChangeView, \
    PasswordChangeDoneView
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CommentForm, SignUpForm, PostForm
from .models import Category, Post, Comment
from .constants import POSTS_PER_PAGE


def index(request):
    """View для главной страницы - вывод последних публикаций."""
    now = timezone.now()

    # Получаем QuerySet опубликованных постов (без get_object_or_404)
    post_list = Post.objects.filter(
        is_published=True,
        pub_date__lte=now,
    ).annotate(
        comment_count=Count('comments')
    ).select_related(
        'category', 'location', 'author'
    )

    # Пагинация
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    """View для страницы отдельной публикации."""
    now = timezone.now()
    post = get_object_or_404(
        Post.objects.filter(
            is_published=True,
            pub_date__lte=now,
        ).select_related(
            'category',
            'location',
            'author'
        ),
        pk=post_id
    )

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
    ).select_related('location', 'author')

    # Добавляем пагинацию
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj  # Передаем page_obj вместо posts
    }
    return render(request, 'blog/category.html', context)

User = get_user_model()


@login_required
def profile(request, username):
    """View для страницы профиля пользователя."""
    profile_user = get_object_or_404(User, username=username)
    now = timezone.now()

    # Получаем все посты пользователя
    post_list = post_list = Post.objects.filter(author=profile_user).annotate(
        comment_count=Count('comments')
    ).select_related('category', 'location')

    # Разделяем посты для автора и других пользователей
    if request.user == profile_user:
        # Автор видит все свои посты (включая отложенные и неопубликованные)
        visible_posts = post_list
    else:
        # Остальные видят только опубликованные с подошедшей датой
        visible_posts = post_list.filter(
            is_published=True,
            pub_date__lte=now
        )

    # Пагинация
    paginator = Paginator(visible_posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile_user,
        'page_obj': page_obj,
        'now': now  # Передаем текущее время для шаблона
    }
    return render(request, 'blog/profile.html', context)


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
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post_id)

    # Если форма не валидна, вернемся на страницу поста
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
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


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user.username])


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        return reverse('post_detail', args=[self.object.id])


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.object
        return context


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


@login_required
def profile_redirect(request):
    """Перенаправление на профиль текущего пользователя"""
    return redirect('blog:profile', username=request.user.username)
