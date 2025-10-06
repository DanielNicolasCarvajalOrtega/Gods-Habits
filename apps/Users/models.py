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



class IAInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ia_conversations')
    PROMPT_TYPES = [
        ('daily_advice', 'Consejo Diario'),
        ('habit_suggestion', 'Sugerencia de Habito'),
        ('motivation','Motivacion'),
        ('analysis','Analisis de Progreso'),
        ('troubleshooting','Solucion de Problemas'),
        ('goal_setting', 'Definicion de Objetivos')
    ]
    prompt_type = models.CharField(max_length=100, choices = PROMPT_TYPES,db_index=True)
    input_data=models.JSONField(
        default=dict
    )
    ai_response = models.TextField()

    FEEDBACK_CHOICES =[
        ('helpful', '👍 Útil'),
        ('not_helpful', '👎 No útil'),
        ('neutral', '😐 Neutral'),
        (None, 'Sin calificar'),
    ]
    user_feedback = models.CharField(
        max_length=100,
        choices=FEEDBACK_CHOICES,
        null=True,
        blank=True
    )
    feedback_comment = models.TextField(
        blank=True,
        help_text="Explica porque..."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user','-created_at']),
            models.Index(fields=['prompt_type','user_feedback']),
        ]

    def __str__(self):
        feedback = self.user_feedback or 'sin evaluar'
        return (f"{self.user.username}"
                f"{self.prompt_type}"
                f"Feedback dado por el usuario: ({feedback})")



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
        validators = [MaxValueValidator(1), MaxValueValidator(100)],
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

