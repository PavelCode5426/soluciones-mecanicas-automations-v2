from django.db import models


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
