from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Habits(models.Model):
    FREQUENCY_CHOICES = [
        ('Daily', 'Diario'),
        ('Weekly', 'Semanal'),

    ]

    PRIORITY_CHOICES = [
        ('Low','Baja'),
        ('Medium','Media'),
        ('High','Alta'),
        ('Very high', 'Muy alta'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="habits")
    title = models.CharField(max_length=260)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    priority = models.TextField(choices=PRIORITY_CHOICES, help_text= "Prioridad del habito")
    target_minutes = models.PositiveIntegerField(
        validators = [MinValueValidator(1), MaxValueValidator(100)],
        help_text = "Duracion en minutos"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active', 'title', 'created_at'])
        ]

    def __str__(self):
        return (f"{self.title} - "
                f"{self.description} - "
                f"{self.is_active}")


class Habit_execution(models.Model):
    STATUS_CHOICES = [
        ('Completed', 'Completada'),
        ('Stand by', 'Pendiente'),
        ('Skipped', 'Omitida'),
        ('Not executed', 'Sin ejecutarse'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ModelUser_executions")
    habit = models.ForeignKey(Habits, on_delete=models.CASCADE, related_name="habits_executions")
    execution_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Not executed")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'habit',
                           'execution_date',
                           'status']
        indexes = [
            models.Index(fields=['user',
                                 'execution_date']),
            models.Index(fields=['habit',
                                 'execution_date']),
        ]

    def __str__(self):
        return (f"{self.habit.title} - "
                f" {self.execution_date} - "
                f"")