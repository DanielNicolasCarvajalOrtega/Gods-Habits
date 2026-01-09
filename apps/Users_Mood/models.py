from time import timezone
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator , MaxValueValidator
from apps.Users.models import ModelUser


class UserMood(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moods')
    date = models.DateField(db_index=True)
    energy_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    stress_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    mood_notes=models.TextField(blank=True ,help_text="Como estuvo tu habito hoy")
    sleep_hours = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True,
        help_text= "Horas de sueño de la noche anterior"
    )
    stress_trigger=models.CharField(
        max_length=120,
        choices=ModelUser.FOCUS_AREA_CHOICES,
        blank=True,
        help_text="¿Que area te esta generando estrés hoy?"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user','-date']),
            models.Index(fields=['energy_level','stress_level'])
        ]

    def __str__(self):
        return (f"{self.user.username} - {self.date}"
                f"Energia {self.energy_level} - Estres {self.stress_level}")
