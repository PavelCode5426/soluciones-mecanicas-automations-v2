from data_fetcher.global_request_context import get_request
from django.db import models


class SoftDeleteQuerySet(models.QuerySet):

    def delete(self):
        return self.update(deleted=True)

    def hard_delete(self):
        return super().delete()

    def restore(self):
        return self.update(deleted=False)


class UserTrackedQuerySet(models.QuerySet):
    def for_user(self):
        user = getattr(get_request(), 'user', None)
        return self.filter(created_by=user)


class SoftDeleteUserTrackedQuerySet(SoftDeleteQuerySet, UserTrackedQuerySet):
    pass


class AllObjectsSoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteManager(AllObjectsSoftDeleteManager):

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class AllObjectsUserTrackedManager(models.Manager):
    def get_queryset(self):
        return UserTrackedQuerySet(self.model, using=self._db)


class UserTrackedManager(AllObjectsUserTrackedManager):
    def get_queryset(self):
        return super().get_queryset().for_user()


class AllObjectsSoftDeleteUserTrackedManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteUserTrackedQuerySet(self.model, using=self._db)


class SoftDeleteUserTrackedManager(AllObjectsSoftDeleteUserTrackedManager):
    def get_queryset(self):
        return super().get_queryset().for_user().filter(deleted=False)
