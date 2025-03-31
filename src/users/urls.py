from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UserLoginView.as_view(), name='login'),
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change_password'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.UpdateProfileView.as_view(), name='profile_edit'),
    path('delete-user/<uuid:user_uuid>/', views.UserDeleteView.as_view(), name='delete_user'),
    path('add-user/', views.AddUserView.as_view(), name='add_user'),
    path('manage-users/', views.ManageUsersView.as_view(), name='manage_users'),
]
