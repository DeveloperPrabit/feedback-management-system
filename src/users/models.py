import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from rental_system.mixins import TimestampMixin
from .managers import UserManager
# Create your models here.

class UserType(models.TextChoices):
    USER = 'user', _('User')
    ADMIN = 'admin', _('Admin')

    

class User(AbstractBaseUser, PermissionsMixin, TimestampMixin):
    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        unique=True,
        default=uuid.uuid4
    )

    email = models.EmailField(
        _('email address'),
        unique=True, 
    )

    full_name = models.CharField(
        _('full name'),
        max_length=100,
        blank=True,
    )

    full_address = models.CharField(
        _('full address'),
        max_length=100,
        blank=True,
    )

    mobile = models.CharField(
        _('mobile'),
        max_length=15,
        blank=True,
    )

    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    is_staff = models.BooleanField(
        default=False
    )

    user_type = models.CharField(
        _('user type'),
        max_length=5,
        choices=UserType.choices,
        default=UserType.USER
    )

    date_joined = models.DateTimeField(
        _('date joined'),
        auto_now_add=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email'], name='email_idx'),
        ]
        ordering = ['-created_at']




