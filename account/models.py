import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from api.models import Land

class Account(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='account_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='account_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)


class Profile(models.Model):
    user = models.ForeignKey(Account, related_name='profile', on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username