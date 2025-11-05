from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='auth_login'),
    path('refresh/', views.refresh_token_view, name='auth_refresh'),
    path('logout/', views.logout_view, name='auth_logout'),
    path('me/', views.me_view, name='auth_me'),
    path('profile/', views.update_profile_view, name='update_profile'),
    path('profile/accept-password/', views.accept_password_view, name='accept_password'),

    # Gestion des utilisateurs (Admin uniquement)
    path('users/', views.users_list_view, name='users_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('users/<int:user_id>/update/', views.user_update_view, name='user_update'),
    path('users/<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
]
