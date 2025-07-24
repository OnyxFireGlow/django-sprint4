from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Comment, Post, Category, Location

User = get_user_model()


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Оставьте ваш комментарий...',
                'class': 'form-textarea'
            })
        }
        labels = {
            'text': ''
        }


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@mail.com',
            'class': 'form-input'
        }),
        label='Адрес электронной почты'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': 'Имя пользователя',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Придумайте логин',
                'class': 'form-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Кастомизация сообщений о помощи
        self.fields['password1'].help_text = 'Минимум 8 \
            имволов, не только цифры'
        self.fields['password2'].help_text = 'Повторите \
            пароль для подтверждения'


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'pub_date', 'location', 'category', 'image']
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'text': forms.Textarea(attrs={'rows': 5,
                                          'class': 'form-textarea'}),
        }
        labels = {
            'pub_date': 'Дата и время публикации',
            'location': 'Местоположение',
            'category': 'Категория',
            'image': 'Изображение',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор только опубликованными категориями
        self.fields['category'].queryset = Category.objects.filter(
            is_published=True)
