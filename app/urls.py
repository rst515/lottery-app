from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .views import (PlayerCreateView, PlayerUpdateView, PlayerDeleteView, DrawCreateView, DrawUpdateView,
                    DrawDeleteView)

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path('hello/', views.HelloView.as_view(), name='hello'),
    path('post-result/', views.PostResult.as_view(), name='post-result'),
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='app/change_password.html'), name='password_change'),
    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='app/change_password_done.html'), name='password_change_done'),
    path("index/", views.index, name="index"),
    path("numbers/", views.numbers, name="numbers"),
    path("numbers/<int:pk>/edit/", views.edit_number__player, name="edit_number__player"),
    path('draw/add/', DrawCreateView.as_view(), name='draw-add'),
    path('draw/<int:pk>/', DrawUpdateView.as_view(), name='draw-update'),
    path('draw/<int:pk>/delete/', DrawDeleteView.as_view(), name='draw-delete'),
    path("players/", views.players, name="players"),
    path('player/add/', PlayerCreateView.as_view(), name='player-add'),
    path('player/<int:pk>/', PlayerUpdateView.as_view(), name='player-update'),
    path('player/<int:pk>/delete/', PlayerDeleteView.as_view(), name='player-delete'),
    path("update_server/", views.update_app, name="update"),
    path("latest_result/", views.latest_result, name="latest_result"),
]
