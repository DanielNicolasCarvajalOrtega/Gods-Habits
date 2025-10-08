from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ModelUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

        # TIPO DE USUARIO
    USER_TYPE_CHOICHES = [
        ('Beginner', 'Principiante'),
        ('Intermediate', 'Intermedio'),
        ('Advanced', 'Avanzado'),
        ('Athlete', 'Deportista Alto Rendimiento'),
        ('Professional', 'Profesional Ocupado'),
        ('Student', 'Estudiante'),
    ]
        # AREAS DE FOCO
    FOCUS_AREA_CHOICES = [
        ('Fitness', 'Entrenamiento Físico'),
        ('Health', 'Salud y Bienestar'),
        ('Learning', 'Lectura y Aprendizaje'),
        ('Work', 'Productividad Laboral'),
        ('Creativity', 'Creatividad y Arte'),
        ('Mindfulness', 'Mindfulness y Meditación'),
        ('Social', 'Relaciones Sociales'),
        ('Finance', 'Finanzas Personales'),
    ]

        # TIEMPO A DEDICAR
    TIME_AVAILABILITY_CHOICES = [
        ('low', 'Poco tiempo (< 1 hora/día)'),
        ('medium', 'Tiempo moderado (1-3 horas/día)'),
        ('high', 'Mucho tiempo (> 3 horas/día)'),
        ('flexible', 'Horario flexible'),
    ]

    user_type = models.CharField(max_length=70, choices=USER_TYPE_CHOICHES)
    created_at = models.DateTimeField(auto_now_add=True)
    first_focus_area = models.CharField(max_length=100, choices=FOCUS_AREA_CHOICES)
    secondary_focus_area = models.JSONField(default=list, blank=True, help_text = "Otras areas de foco")
    daily_time_availability = models.CharField(max_length=100, choices = TIME_AVAILABILITY_CHOICES)
    preferred_morning_time = models.TimeField(null=True, blank=True, help_text = "Horas preferidas por la mañana")
    preferred_evening_time = models.TimeField(null=True, blank=True, help_text = "Horas preferidas por la tarde")
    motivation_level = models.IntegerField(
        validators = [MinValueValidator(1),   MaxValueValidator(20)],
        help_text = "Nivel de motivacion de 1 ha 10"
    )

    user_objective = models.TextField(help_text="Objetivos principales del usuario")
    experience_level_user = models.IntegerField(
        validators = [MinValueValidator(1), MaxValueValidator(20)],
        default = 1,
        help_text = "Nivel de experiencia del usuario"
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"


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

    class meta:
        unique_together = ['user','date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user','-date']),
            models.Index(fields=['energy_level','sterss_level'])
        ]

    def __str__(self):
        return (f"{self.user.username} - {self.date}"
                f"Energia {self.energy_level} - Estres {self.stress_level}")









