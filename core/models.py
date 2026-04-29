from crum import get_current_user
from django.contrib.auth import get_user_model
from django.db import models

from core.managers import SoftDeleteManager, UserTrackedManager, SoftDeleteUserTrackedManager, \
    AllObjectsSoftDeleteUserTrackedManager, AllObjectsUserTrackedManager, AllObjectsSoftDeleteManager

User = get_user_model()


class SoftDeleteModel(models.Model):
    deleted = models.BooleanField(default=False, editable=False)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        editable=False
    )
    objects = SoftDeleteManager()
    all_objects = AllObjectsSoftDeleteManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        current_user = get_current_user()
        self.deleted = True
        if current_user:
            self.deleted_by = current_user
        self.save()

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.deleted = False
        self.deleted_by = None
        self.save()


class UserTrackedModel(models.Model):
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        editable=False
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        editable=False
    )

    objects = UserTrackedManager()
    all_objects = AllObjectsUserTrackedManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_user = get_current_user()
        if not self.pk:
            if current_user:
                self.created_by = current_user
        if current_user:
            self.updated_by = current_user
        super().save(*args, **kwargs)


class SoftDeleteUserTrackedModel(UserTrackedModel, SoftDeleteModel):
    objects = SoftDeleteUserTrackedManager()
    all_objects = AllObjectsSoftDeleteUserTrackedManager()

    class Meta:
        abstract = True


# Create your models here.
class WeekDay(models.Model):
    name = models.CharField(max_length=25)
    day = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Día"
        verbose_name_plural = "Días"


class Media(models.Model):
    name = models.CharField(max_length=25)
    file = models.FileField(upload_to='medias')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Schedule(models.Model):
    name = models.CharField(max_length=100)
    time = models.TimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        ordering = ['time']
