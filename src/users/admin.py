from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User

# Register your models here.

class UserAdmin(UserAdmin):
    model = User
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = ("email", "is_staff", "is_active")
    list_filter = ("email", "is_staff", "is_active")

    fieldsets = (
        ('General', {
            "fields": (
                "email", "password"
            )}
        ),
        ("Personal Information", {
            "fields": (
                "full_name", "full_address", "mobile", "profile_picture"
            )
        }),
        ("Permissions", {
            "fields": (
                "is_staff", "is_active", "user_type", "groups", "user_permissions"
            )}
        ),
    )

    add_fieldsets = (
        ('General', {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2"
            )}
        ),
        ("Personal Information", {
            "fields": (
                "full_name", "full_address", "mobile", "profile_picture"
            )}
        ),
        ("Permissions", {
            "classes": ("wide",),
            "fields": (
                "is_staff", "is_active", "user_type", "groups", "user_permissions"
            )}
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)

admin.site.register(User, UserAdmin)
