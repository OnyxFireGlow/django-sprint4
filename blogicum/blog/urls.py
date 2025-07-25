from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),

    # Посты (без ID)
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),

    # Посты (с ID)
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/edit/',
         views.PostUpdateView.as_view(), name='edit_post'),
    path('posts/<int:post_id>/delete/',
         views.PostDeleteView.as_view(), name='delete_post'),

    # Комментарии
    path('posts/<int:post_id>/comment/', views.add_comment, name='add_\
         comment'),
    path('posts/<int:post_id>/edit_comment/<int:comment_id>/',
         views.edit_comment, name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<int:comment_id>/',
         views.delete_comment, name='delete_comment'),

    # Категории
    path('category/<slug:category_slug>/',
         views.category_posts, name='category_posts'),

    # Профиль
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='edit_\
         profile'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/', views.profile_redirect, name='profile_redirect'),

    # Пароль
    path('password_change/', views.CustomPasswordChangeView.as_view(),
         name='password_change'),
    path('password_change/done/', views.CustomPasswordChangeDoneView.as_view(),
         name='password_change_done'),
]
