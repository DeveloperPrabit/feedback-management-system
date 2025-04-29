import uuid
import random
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.core.exceptions import ValidationError
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




class PasswordResetOTP(TimestampMixin):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_otps'
    )

    otp = models.CharField(
        max_length=6,
    )

    def is_valid(self):
        return timezone.now() <= (self.updated_at + timedelta(minutes=60))
    

class SystemLogo(TimestampMixin):
    logo = models.ImageField(
        upload_to='system_logo/',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"System Logo {self.id}"

    class Meta:
        verbose_name = _('system logo')
        verbose_name_plural = _('system logos')
        ordering = ['-created_at']
    


class Contact(TimestampMixin):
    email = models.EmailField(
        _('email address'),
        unique=True, 
    )

    phone = models.CharField(
        _('phone number'),
        max_length=15,
    )

    address = models.CharField(
        _('address'),
        max_length=255,
        blank=True,
    )


    def __str__(self):
        return self.email
    
    def clean(self):
        super().clean()
        if not self.pk and self.__class__.objects.exists():
            raise ValidationError(_('Only one contact information can be created.'))
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)