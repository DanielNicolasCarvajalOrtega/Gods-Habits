from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


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